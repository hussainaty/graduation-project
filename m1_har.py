"""Fit and evaluate the price-only M1 models using daily adjusted closes."""

from dataclasses import dataclass
from math import ceil, sqrt
from pathlib import Path
import re

import numpy as np
import pandas as pd

from m1_evaluation import (
    adaptive_ranges,
    best_on_validation,
    combination_points,
    conformal_radius,
    dm_test,
    summarize_results,
)
from m1_garch import GARCH_MODELS, garch_features


ROOT = Path(__file__).resolve().parent
PRICES = ROOT / "prices"
RESULTS = ROOT / "results"
START = pd.Timestamp("2013-01-01")
TEST_START = pd.Timestamp("2022-01-01")
HORIZONS = (1, 5, 20)
WINDOWS = (1, 5, 22)
OHLC = ("Open", "High", "Low", "Close")
ENSEMBLE_MEMBERS = ("HAR", "LHAR", "HAR-RANGE", "GJR-GARCH")
HARQ_NOTE = (
    "HARQ was skipped because daily OHLCV cannot estimate intraday quarticity. "
    "A single daily return to the fourth power simply squares the daily variance proxy."
)
LOG_FLOOR = 1e-8
ADAPTIVE_COLUMNS = ["lo_adaptive", "hi_adaptive"]
FORECAST_COLUMNS = ["date", "horizon", "actual", "point", "lo", "hi"]
METRIC_COLUMNS = [
    "ticker", "horizon", "model", "MAE", "RMSE", "coverage_90", "avg_width", "n_test",
    "dm_stat", "dm_pvalue_vs_har", "coverage_90_adaptive", "avg_width_adaptive",
    "unbounded_rate_adaptive", "adaptive_role",
]


@dataclass
class Evaluation:
    metrics: pd.DataFrame
    test: pd.DataFrame
    latest: pd.DataFrame
    issues: list[str]
    best_combinations: dict[int, str]


def read_tickers() -> list[str]:
    lines = (ROOT / "tickers.txt").read_text(encoding="utf-8-sig").splitlines()
    tickers = (line.partition("#")[0].strip().upper() for line in lines)
    return list(dict.fromkeys(ticker for ticker in tickers if ticker))


def ticker_filename(ticker: str) -> str:
    # Yahoo symbols can contain exchange suffixes, hyphens, or a prefix such as ^.
    if not re.fullmatch(r"[A-Z0-9^][A-Z0-9.^=_-]*", ticker):
        raise ValueError("Enter a valid Yahoo Finance ticker, such as COMI.CA.")
    return ticker.replace(".", "_")


def read_cached_prices(ticker: str) -> pd.DataFrame:
    return pd.read_csv(PRICES / (ticker_filename(ticker) + ".csv")).set_index("date")


def download_prices(ticker: str) -> pd.DataFrame:
    import yfinance as yf

    ticker_filename(ticker)
    prices = yf.download(
        ticker, start=START.date().isoformat(), interval="1d", auto_adjust=False,
        progress=False, multi_level_index=False, threads=False, timeout=10,
    )
    if prices.empty:
        raise ValueError(f"Yahoo Finance returned no daily prices for {ticker}.")
    return prices


def prepare_prices(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    required = ["Adj Close", "Volume"]
    missing = set(required).difference(raw.columns)
    if missing:
        raise ValueError(f"Missing price columns: {', '.join(sorted(missing))}")

    dates = pd.to_datetime(raw.index, errors="coerce", utc=True).tz_convert(None).normalize()
    # Keep optional OHLC for range and overnight features. Target days depend only on adjusted close and volume.
    prices = raw.reindex(columns=[*required, *OHLC]).apply(pd.to_numeric, errors="coerce").set_axis(dates)
    prices[list(OHLC)] = prices[list(OHLC)].where(np.isfinite(prices[list(OHLC)]) & prices[list(OHLC)].gt(0))
    prices.index.name = "date"
    bad_dates = int(prices.index.isna().sum())
    prices = prices.loc[prices.index >= START]
    duplicates = int(prices.index.duplicated(keep="last").sum())
    prices = prices.loc[~prices.index.duplicated(keep="last")].sort_index()
    stale = prices["Volume"].eq(0)
    usable = (
        np.isfinite(prices[required]).all(axis=1)
        & prices["Adj Close"].gt(0)
        & prices["Volume"].gt(0)
    )
    invalid = int((~usable & ~stale).sum())
    issues = []
    if bad_dates or duplicates or invalid:
        issues.append(
            f"Excluded {bad_dates} invalid dates, {duplicates} duplicate dates, "
            f"and {invalid} other invalid price or volume rows."
        )
    if stale.any():
        issues.append(f"Excluded {int(stale.sum())} zero-volume rows since {START.date()}.")
    return prices.loc[usable], issues


def make_features(log_price: pd.Series) -> pd.DataFrame:
    magnitude = log_price.diff().abs()
    return pd.DataFrame({window: magnitude.rolling(window).mean() for window in WINDOWS}).dropna()


def split_horizon(
    features: pd.DataFrame, log_price: pd.Series, horizon: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    target = log_price.shift(-horizon).sub(log_price).abs().rename("actual")
    target_date = log_price.index.to_series().shift(-horizon).rename("target_date")
    labeled = features.join(target).join(target_date).dropna(subset=["actual"])
    train = labeled.loc[labeled["target_date"] < TEST_START]
    test = labeled.loc[labeled.index >= TEST_START]

    n_calibration = ceil(len(train) / 5)
    calibration = train.tail(n_calibration)
    fit = train.head(len(train) - n_calibration)
    if not calibration.empty:
        fit = fit.loc[fit["target_date"] < calibration.index[0]]
    return fit, calibration, test


def trailing_features(series: pd.Series, name: str) -> pd.DataFrame:
    return pd.DataFrame({f"{name}_{w}": series.rolling(w).mean() for w in WINDOWS})


def load_watchlist() -> tuple[dict[str, pd.DataFrame], list[str]]:
    cached = {}
    issues = []
    for ticker in read_tickers():
        try:
            prices, notes = prepare_prices(read_cached_prices(ticker))
        except (OSError, ValueError, KeyError) as error:
            issues.append(f"{ticker}: {error}")
            continue
        cached[ticker] = prices
        issues.extend(f"{ticker}: {note}" for note in notes)
    return cached, issues


def market_volatility(prices_by_ticker: dict[str, pd.DataFrame]) -> pd.Series:
    returns = [np.log(prices["Adj Close"]).diff().abs() for prices in prices_by_ticker.values()]
    if not returns:
        return pd.Series(dtype=float, index=pd.DatetimeIndex([]))
    return pd.concat(returns, axis=1, sort=True).mean(axis=1).dropna().rename("market_vol")


def price_features(
    prices: pd.DataFrame, log_price: pd.Series, market: pd.Series,
) -> tuple[pd.DataFrame, dict[str, list]]:
    returns = log_price.diff()
    har = make_features(log_price)
    squared = trailing_features(returns.pow(2), "rv")
    high_low = np.log(prices["High"]).sub(np.log(prices["Low"]))
    high_low = high_low.where(high_low.ge(0))
    open_close = np.log(prices["Close"]).sub(np.log(prices["Open"]))
    parkinson = trailing_features(high_low.pow(2) / (4 * np.log(2)), "parkinson")
    garman_klass = 0.5 * high_low.pow(2) - (2 * np.log(2) - 1) * open_close.pow(2)
    garman_klass = trailing_features(garman_klass.clip(lower=0), "garman_klass")
    log_volume = np.log(prices["Volume"])
    x = pd.DataFrame({
        "lagged_volume": log_volume.shift(1) - log_volume.shift(2).rolling(22).mean(),
        "overnight_gap": np.log(prices["Open"]).sub(np.log(prices["Close"]).shift(1)).abs(),
        "market_vol": market.reindex(prices.index, method="ffill"),
        "negative_return": returns.lt(0).astype(float),
    }, index=prices.index)
    log_har = np.log(har.clip(lower=LOG_FLOOR)).add_prefix("log_")
    features = har.join([log_har, squared, parkinson, garman_klass, x])
    designs = {
        "HAR": list(WINDOWS),
        "Log-HAR": log_har.columns.tolist(),
        "HAR-RV": squared.columns.tolist(),
        "HAR-RANGE": [*parkinson.columns, *garman_klass.columns],
        "LHAR": [*WINDOWS, "negative_return"],
        "HAR-X": [*WINDOWS, *x.columns],
    }
    return features, designs


def regression_points(fit: pd.DataFrame, inputs: pd.DataFrame, columns: list) -> pd.Series:
    training = fit[[*columns, "actual"]].dropna()
    if len(training) < len(columns) + 1:
        return pd.Series(np.nan, index=inputs.index)
    x = training[columns].to_numpy()
    design = np.column_stack((np.ones(len(x)), x))
    coefficients = np.linalg.lstsq(design, training["actual"].to_numpy(), rcond=None)[0]
    point = np.maximum(0, coefficients[0] + inputs[columns].to_numpy() @ coefficients[1:])
    return pd.Series(point, index=inputs.index)


def calibrated_combinations(
    individual: pd.DataFrame, calibration: pd.DataFrame, issues: list[str],
) -> tuple[pd.DataFrame, pd.Index, str | None, str | None]:
    conformal_start = calibration.index[len(calibration) // 2]
    weight_rows = calibration.loc[calibration["target_date"] < conformal_start]
    conformal_dates = calibration.loc[conformal_start:].index

    # Early calibration validates the model choice, with a separate earlier weight fit.
    validation_start = weight_rows.index[len(weight_rows) * 2 // 3] if not weight_rows.empty else conformal_start
    validation = weight_rows.loc[validation_start:, "actual"]
    selection_targets = weight_rows.loc[weight_rows["target_date"] < validation_start, "actual"]
    best_individual = best_on_validation(individual, validation) or "HAR"
    members = [model for model in ENSEMBLE_MEMBERS if model in individual]
    if len(members) < 3 or tuple(members[:3]) != ENSEMBLE_MEMBERS[:3]:
        issues.append("Combinations were skipped because a required HAR-family forecast was unavailable.")
        return individual, conformal_dates, best_individual, None

    combos = combination_points(individual, weight_rows["actual"], members)
    validation_combos = combination_points(individual, selection_targets, members)
    best_combo = best_on_validation(validation_combos, validation) or combos.columns[0]
    if best_combo not in combos:
        best_combo = combos.columns[0]
    return individual.join(combos), conformal_dates, best_individual, best_combo


def forecast_metrics(
    ticker: str, horizon: int, model: str, backtest: pd.DataFrame, har: pd.Series,
    adaptive_role: str | None,
) -> dict:
    actual, point = backtest["actual"], backtest["point"]
    errors = (actual - point).abs()
    statistic = pvalue = np.nan
    if model != "HAR":
        baseline_errors = (actual - har.reindex(backtest.index)).abs()
        statistic, pvalue = dm_test((errors - baseline_errors).dropna().to_numpy(), horizon)
    row = {
        "ticker": ticker, "horizon": horizon, "model": model, "MAE": errors.mean(),
        "RMSE": np.sqrt(errors.pow(2).mean()),
        "coverage_90": actual.between(backtest["lo"], backtest["hi"]).mean(),
        "avg_width": (backtest["hi"] - backtest["lo"]).mean(), "n_test": len(backtest),
        "dm_stat": statistic, "dm_pvalue_vs_har": pvalue,
        "adaptive_role": adaptive_role,
    }
    if adaptive_role:
        lower, upper = (backtest[column] for column in ADAPTIVE_COLUMNS)
        row.update(
            coverage_90_adaptive=actual.between(lower, upper).mean(),
            avg_width_adaptive=(upper - lower).clip(lower=0).mean(),
            unbounded_rate_adaptive=np.isposinf(upper).mean(),
        )
    return row


def evaluate_ticker(
    ticker: str, prices: pd.DataFrame, market: pd.Series | None = None,
) -> Evaluation:
    if market is None:
        watchlist, _ = load_watchlist()
        if ticker in watchlist:
            watchlist[ticker] = prices
        market = market_volatility(watchlist)
    log_price = np.log(prices["Adj Close"])
    features, designs = price_features(prices, log_price, market)
    splits = {h: split_horizon(features, log_price, h) for h in HORIZONS}
    eligible = {h: split for h, split in splits.items()
                if len(split[0]) >= len(WINDOWS) + 1 and len(split[1]) >= 9}
    garch, hybrid, issues = {}, pd.DataFrame(), []
    if eligible:
        first_calibration = min(split[1].index[0] for split in eligible.values())
        garch, hybrid, issues = garch_features(log_price.diff(), first_calibration, tuple(eligible))
    metrics, test_rows, latest_rows = [], [], []
    best_combinations = {}

    for horizon, (fit, calibration, test) in splits.items():
        if horizon not in eligible:
            issues.append(
                f"Horizon {horizon} has insufficient pre-2022 history "
                f"({len(fit)} fit rows, {len(calibration)} calibration rows)."
            )
            continue

        timeline = features.loc[features.index >= TEST_START].join(test[["actual", "target_date"]])
        if test.empty:
            issues.append(f"Horizon {horizon} has no realized test targets.")
        inputs = pd.concat([calibration, timeline])
        points = pd.DataFrame({name: regression_points(fit, inputs, cols)
                               for name, cols in designs.items()})
        points["Naive"] = inputs[22] * sqrt(horizon)
        for name, series in garch.items():
            points[name] = series[horizon].reindex(inputs.index)
        if not hybrid.empty:
            vol = hybrid[horizon].rename("garch_vol")
            points["HAR-GARCH"] = regression_points(
                fit.join(vol), inputs.join(vol), [*designs["HAR-X"], "garch_vol"],
            )

        cal_points = points.reindex(calibration.index)
        unavailable = cal_points.count().loc[lambda counts: counts.lt(9)].index
        issues.extend(f"{name} has fewer than nine calibration predictions at horizon {horizon}."
                      for name in unavailable)
        points, conformal_dates, best_individual, best_combo = calibrated_combinations(
            points.drop(columns=unavailable), calibration, issues,
        )
        if best_combo is not None:
            best_combinations[horizon] = best_combo

        for name in points:
            learned_combo = name.startswith(("Combo Inv-MSE", "Combo Ridge"))
            dates = conformal_dates if learned_combo else calibration.index
            scores = (points.loc[dates, name] - calibration.loc[dates, "actual"]).abs().dropna()
            if len(scores) < 9:
                issues.append(f"{name} has too few held-out conformal residuals at horizon {horizon}.")
                if best_combinations.get(horizon) == name:
                    best_combinations.pop(horizon)
                continue

            radius = conformal_radius(scores.to_numpy())
            forecasts = timeline[["actual", "target_date"]].join(points[name].rename("point"))
            forecasts = forecasts.dropna(subset=["point"])
            forecasts["lo"] = (forecasts["point"] - radius).clip(lower=0)
            forecasts["hi"] = forecasts["point"] + radius
            forecasts["horizon"] = horizon
            forecasts["model"] = name
            forecasts["lo_adaptive"] = forecasts["hi_adaptive"] = np.nan
            role = "Combination" if name == best_combo else "Individual" if name == best_individual else None
            if role is not None:
                forecasts["lo_adaptive"], forecasts["hi_adaptive"] = adaptive_ranges(forecasts, scores.to_numpy())

            backtest = forecasts.dropna(subset=["actual"])
            if not backtest.empty:
                metrics.append(forecast_metrics(ticker, horizon, name, backtest, points["HAR"], role))
                test_rows.append(backtest.reset_index())
            if not timeline.empty and timeline.index[-1] in forecasts.index:
                latest_rows.append(forecasts.tail(1).reset_index())

    columns = [*FORECAST_COLUMNS, "model", *ADAPTIVE_COLUMNS]
    return Evaluation(
        pd.DataFrame(metrics, columns=METRIC_COLUMNS),
        pd.concat(test_rows, ignore_index=True)[columns] if test_rows else pd.DataFrame(columns=columns),
        pd.concat(latest_rows, ignore_index=True)[columns] if latest_rows else pd.DataFrame(columns=columns),
        list(dict.fromkeys(issues)),
        best_combinations,
    )


def write_summary(metrics: pd.DataFrame, summary: pd.DataFrame, issues: list[str]) -> None:
    lines = [
        "# M1 results",
        "",
        "The backtest forecasts absolute adjusted-close log returns for 1, 5, and 20 retained sessions.",
        "Average MAE rank gives each ticker equal weight within a horizon. Rank 1 is best.",
        "Diebold–Mariano counts use paired absolute errors, a two-sided 5% threshold, and "
        "Newey–West variance with h−1 lags. The p-values are unadjusted for multiple comparisons.",
        "",
        "## Model rankings",
        "",
        "| Sessions | Model | Avg. MAE rank | Mean MAE | Tickers | Significant wins vs HAR | Significant losses vs HAR |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.horizon} | {row.model} | {row.avg_mae_rank:.2f} | {row.mean_MAE:.2%} | "
            f"{row.n_tickers} | {row.significant_wins_vs_har} | {row.significant_losses_vs_har} |"
        )
    lines.extend(["", "## What performed best", ""])
    for horizon, rows in summary.groupby("horizon"):
        rank = rows["avg_mae_rank"].min()
        leaders = rows.loc[rows["avg_mae_rank"].eq(rank), "model"].tolist()
        sessions = "session" if horizon == 1 else "sessions"
        if len(leaders) > 1:
            lines.append(f"- {' and '.join(leaders)} tied for the lowest average rank at {horizon} {sessions} ({rank:.2f}).")
        else:
            lines.append(f"- {leaders[0]} had the lowest average rank at {horizon} {sessions} ({rank:.2f}).")
    comparison = summary.loc[summary["model"].isin(["HAR-X", *GARCH_MODELS, "HAR-GARCH"])]
    har_rank = summary.loc[summary["model"].eq("HAR")].set_index("horizon")["avg_mae_rank"]
    for model, group in comparison.groupby("model"):
        ranked_better = group["avg_mae_rank"].lt(group["horizon"].map(har_rank)).sum()
        detail = ", ".join(
            f"{row.horizon}-session {row.significant_wins_vs_har}/{row.n_tickers} wins "
            f"and {row.significant_losses_vs_har}/{row.n_tickers} losses"
            for row in group.itertuples(index=False)
        )
        lines.append(
            f"- {model} ranked ahead of HAR at {ranked_better}/{len(group)} horizons. "
            f"Significant ticker comparisons at the 5% threshold were {detail}."
        )
    missing_garch = set(GARCH_MODELS).difference(metrics["model"])
    if missing_garch:
        lines.append(f"- No test comparison is available for {', '.join(sorted(missing_garch))}.")
    if summary.empty:
        lines.append("No ticker had enough data for evaluation.")

    lines.extend([
        "", "## Adaptive coverage", "",
        "Each ticker and horizon chooses an individual model and a combination using pre-2022 validation MAE. "
        "The rows below compare both intervals on exactly those selected forecasts.",
        "Adaptive updates use gamma 0.005 after the h-session outcome is observed.",
        "",
        "| Sessions | Selected model type | Tickers | Standard coverage | Adaptive coverage | Unbounded adaptive share |",
        "|---:|---|---:|---:|---:|---:|",
    ])
    for (horizon, role), rows in metrics.groupby(["horizon", "adaptive_role"]):
        fixed = rows["coverage_90"].mean()
        adaptive = rows["coverage_90_adaptive"].mean()
        unbounded = rows["unbounded_rate_adaptive"].mean()
        lines.append(f"| {horizon} | {role} | {len(rows)} | {fixed:.1%} | {adaptive:.1%} | {unbounded:.1%} |")
    selected = metrics.dropna(subset=["coverage_90_adaptive"])
    if not selected.empty:
        fixed, adaptive = selected[["coverage_90", "coverage_90_adaptive"]].mean()
        reached = selected["coverage_90_adaptive"].ge(0.90).sum()
        lines.extend([
            "",
            f"Across selected ticker and horizon pairs, mean coverage changed from {fixed:.1%} to {adaptive:.1%}. "
            f"{reached}/{len(selected)} pairs reached 90% adaptive coverage. Unbounded intervals cover "
            "every move and are included in both coverage and mean width.",
        ])

    lines.extend([
        "", "## Data and model notes", "",
        "- Forecast CSVs retain the standard HAR backtest and the original six columns.",
        "- A three-member combination uses HAR, LHAR, and HAR-RANGE when a GJR-GARCH forecast is unavailable.",
        f"- {HARQ_NOTE}",
        *(f"- {issue.replace(': ', ' — ', 1)}" for issue in dict.fromkeys(issues)),
    ])
    (RESULTS / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS.mkdir(exist_ok=True)
    watchlist, issues = load_watchlist()
    market = market_volatility(watchlist)
    tables = []
    for ticker in read_tickers():
        filename = RESULTS / f"forecasts_{ticker_filename(ticker)}.csv"
        if ticker not in watchlist:
            pd.DataFrame(columns=FORECAST_COLUMNS).to_csv(filename, index=False)
            continue

        evaluation = evaluate_ticker(ticker, watchlist[ticker], market)
        if not evaluation.metrics.empty:
            tables.append(evaluation.metrics)
        issues.extend(note if note.startswith("arch is unavailable") else f"{ticker}: {note}"
                      for note in evaluation.issues)
        har = evaluation.test.loc[evaluation.test["model"].eq("HAR"), FORECAST_COLUMNS]
        har.to_csv(filename, index=False)

    metrics = pd.concat(tables, ignore_index=True) if tables else pd.DataFrame(columns=METRIC_COLUMNS)
    summary = summarize_results(metrics)
    metrics.to_csv(RESULTS / "m1_results.csv", index=False)
    summary.to_csv(RESULTS / "m1_summary.csv", index=False)
    write_summary(metrics, summary, issues)
    for issue in dict.fromkeys(issues):
        print(issue)
    print()
    print(summary.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
    return 0 if tables else 1


if __name__ == "__main__":
    raise SystemExit(main())
