"""Fit and evaluate the price-only M1 models using daily adjusted closes."""

from dataclasses import dataclass
from math import ceil, sqrt
from pathlib import Path
import re

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
PRICES = ROOT / "prices"
RESULTS = ROOT / "results"
START = pd.Timestamp("2013-01-01")
TEST_START = pd.Timestamp("2022-01-01")
HORIZONS = (1, 5, 20)
WINDOWS = (1, 5, 22)
MODELS = ("HAR", "Log-HAR", "Naive")
LOG_FLOOR = 1e-8
FORECAST_COLUMNS = ["date", "horizon", "actual", "point", "lo", "hi"]
METRIC_COLUMNS = [
    "ticker", "horizon", "model", "MAE", "RMSE", "coverage_90", "avg_width", "n_test",
]


@dataclass
class Evaluation:
    metrics: pd.DataFrame
    test: pd.DataFrame
    latest: pd.DataFrame
    issues: list[str]


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
    prices = raw[required].apply(pd.to_numeric, errors="coerce").set_axis(dates)
    prices.index.name = "date"
    bad_dates = int(prices.index.isna().sum())
    prices = prices.loc[prices.index >= START]
    duplicates = int(prices.index.duplicated(keep="last").sum())
    prices = prices.loc[~prices.index.duplicated(keep="last")].sort_index()
    stale = prices["Volume"].eq(0)
    usable = (
        np.isfinite(prices).all(axis=1)
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


def point_forecasts(
    model: str, fit: pd.DataFrame, features: pd.DataFrame, horizon: int,
) -> np.ndarray:
    if model == "Naive":
        return features[22].to_numpy() * sqrt(horizon)

    x_fit = fit[list(WINDOWS)].to_numpy()
    x = features[list(WINDOWS)].to_numpy()
    if model == "Log-HAR":
        x_fit = np.log(np.maximum(x_fit, LOG_FLOOR))
        x = np.log(np.maximum(x, LOG_FLOOR))
    design = np.column_stack((np.ones(len(x_fit)), x_fit))
    coefficients = np.linalg.lstsq(design, fit["actual"].to_numpy(), rcond=None)[0]
    return np.maximum(0, coefficients[0] + x @ coefficients[1:])


def conformal_radius(scores: np.ndarray) -> float:
    """Use the finite-sample split conformal order statistic."""
    rank = ceil(9 * (len(scores) + 1) / 10)
    if rank > len(scores):
        raise ValueError("A finite 90% conformal range needs at least 9 calibration rows.")
    return float(np.partition(scores, rank - 1)[rank - 1])


def evaluate_ticker(ticker: str, prices: pd.DataFrame) -> Evaluation:
    log_price = np.log(prices["Adj Close"])
    features = make_features(log_price)
    latest = features.loc[features.index >= TEST_START].tail(1)
    metrics = []
    test_forecasts = []
    latest_forecasts = []
    issues = []

    for horizon in HORIZONS:
        fit, calibration, test = split_horizon(features, log_price, horizon)
        if len(fit) < len(WINDOWS) + 1 or len(calibration) < 9:
            issues.append(
                f"Horizon {horizon} has insufficient pre-2022 history "
                f"({len(fit)} fit rows, {len(calibration)} calibration rows)."
            )
            continue
        if test.empty:
            issues.append(f"Horizon {horizon} has no realized test targets.")

        # Predict on one design matrix so each model is fitted exactly once per horizon.
        inputs = pd.concat([calibration, test, latest], sort=False)
        for model in MODELS:
            points = point_forecasts(model, fit, inputs, horizon)
            radius = conformal_radius(
                np.abs(calibration["actual"].to_numpy() - points[:len(calibration)])
            )
            forecasts = inputs.iloc[len(calibration):][["actual"]].copy()
            forecasts["point"] = points[len(calibration):]
            forecasts["lo"] = (forecasts["point"] - radius).clip(lower=0)
            forecasts["hi"] = forecasts["point"] + radius
            forecasts["horizon"] = horizon
            forecasts["model"] = model
            forecasts = forecasts.reset_index()

            if not latest.empty:
                newest = forecasts.tail(1).copy()
                newest["actual"] = np.nan
                latest_forecasts.append(newest)
            backtest = forecasts.head(len(test))
            if not backtest.empty:
                test_forecasts.append(backtest)
                error = backtest["actual"] - backtest["point"]
                metrics.append({
                    "ticker": ticker,
                    "horizon": horizon,
                    "model": model,
                    "MAE": error.abs().mean(),
                    "RMSE": np.sqrt(error.pow(2).mean()),
                    "coverage_90": backtest["actual"].between(backtest["lo"], backtest["hi"]).mean(),
                    "avg_width": (backtest["hi"] - backtest["lo"]).mean(),
                    "n_test": len(backtest),
                })
    columns = [*FORECAST_COLUMNS, "model"]
    return Evaluation(
        pd.DataFrame(metrics, columns=METRIC_COLUMNS),
        pd.concat(test_forecasts, ignore_index=True) if test_forecasts else pd.DataFrame(columns=columns),
        pd.concat(latest_forecasts, ignore_index=True) if latest_forecasts else pd.DataFrame(columns=columns),
        issues,
    )


def write_summary(metrics: pd.DataFrame, issues: list[str]) -> None:
    lines = [
        "# M1 results",
        "",
        "M1 predicts absolute adjusted-close log returns for 1, 5, and 20 retained trading sessions.",
        "Forecast CSVs show the HAR backtest by forecast origin. m1_results.csv includes all three models.",
        "Errors and widths are in decimal log-return units. Coverage is the fraction of test outcomes inside the range.",
        "",
        "## Mean across ticker and horizon pairs",
        "",
        "| Model | MAE | RMSE | Coverage | Average width |",
        "|---|---:|---:|---:|---:|",
    ]
    for model, rows in metrics.groupby("model", sort=False):
        lines.append(
            f"| {model} | {100 * rows['MAE'].mean():.2f}% | {100 * rows['RMSE'].mean():.2f}% | "
            f"{rows['coverage_90'].mean():.1%} | {100 * rows['avg_width'].mean():.2f}% |"
        )
    if metrics.empty:
        lines.extend(["", "No ticker had enough data for evaluation."])
    if issues:
        lines.extend(["", "## Data and evaluation notes", "", *(f"- {issue}" for issue in issues)])
    (RESULTS / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS.mkdir(exist_ok=True)
    tables = []
    issues = []
    for ticker in read_tickers():
        filename = RESULTS / f"forecasts_{ticker_filename(ticker)}.csv"
        try:
            prices, data_issues = prepare_prices(read_cached_prices(ticker))
        except (OSError, ValueError, KeyError) as error:
            issues.append(f"{ticker} — {error}")
            pd.DataFrame(columns=FORECAST_COLUMNS).to_csv(filename, index=False)
            continue

        evaluation = evaluate_ticker(ticker, prices)
        if not evaluation.metrics.empty:
            tables.append(evaluation.metrics)
        issues.extend(f"{ticker} — {issue}" for issue in data_issues + evaluation.issues)
        har = evaluation.test.loc[evaluation.test["model"].eq("HAR"), FORECAST_COLUMNS]
        har.to_csv(filename, index=False)

    metrics = pd.concat(tables, ignore_index=True) if tables else pd.DataFrame(columns=METRIC_COLUMNS)
    metrics.to_csv(RESULTS / "m1_results.csv", index=False)
    write_summary(metrics, issues)
    for issue in issues:
        print(issue)
    print()
    print(metrics.to_string(index=False, float_format=lambda value: f"{value:.5f}"))
    return 0 if tables else 1


if __name__ == "__main__":
    raise SystemExit(main())
