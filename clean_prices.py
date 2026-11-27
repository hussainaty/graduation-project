"""Build split-adjusted EGX price returns and audit anomalous sessions."""

from dataclasses import dataclass
from pathlib import Path
import re

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
OHLC = ("Open", "High", "Low", "Close")
ACTION_COLUMNS = ("Dividends", "Stock Splits")
ISSUE_COLUMNS = ("ticker", "date", "reason_code", "source", "reference_date", "ratio", "log_return", "detail")
SPLIT_TOLERANCE = 0.08
LARGE_MOVE = 0.20


@dataclass(frozen=True)
class Split:
    date: pd.Timestamp
    ratio: float
    source: str
    note: str = ""


def read_tickers() -> list[str]:
    lines = (ROOT / "tickers.txt").read_text(encoding="utf-8-sig").splitlines()
    tickers = (line.partition("#")[0].strip().upper() for line in lines)
    return list(dict.fromkeys(ticker for ticker in tickers if ticker))


def ticker_filename(ticker: str) -> str:
    if not re.fullmatch(r"[A-Z0-9^][A-Z0-9.^=_-]*", ticker):
        raise ValueError("Enter a valid Yahoo Finance ticker, such as COMI.CA.")
    return ticker.replace(".", "_")


def read_raw_prices(ticker: str) -> pd.DataFrame:
    return pd.read_csv(ROOT / "prices" / f"{ticker_filename(ticker)}.csv").set_index("date")


def normalize_dates(index) -> pd.DatetimeIndex:
    dates = pd.to_datetime(index, errors="coerce")
    # Action timestamps are in the exchange's timezone. Keep the calendar date.
    return dates.tz_localize(None).normalize().rename("date")


def manual_splits(ticker: str) -> list[Split]:
    path = ROOT / "corporate_actions_manual.csv"
    if not path.exists():
        return []
    table = pd.read_csv(path, comment="#")
    selected = table.loc[table["ticker"].str.strip().str.upper().eq(ticker)]
    splits = []
    for row in selected.itertuples(index=False):
        date = pd.to_datetime(row.date, errors="coerce")
        ratio = float(row.ratio)
        if pd.isna(date) or not np.isfinite(ratio) or ratio <= 0 or ratio == 1:
            raise ValueError(f"Invalid manual split for {ticker} on {row.date!r}.")
        note = str(row.note) if pd.notna(row.note) else ""
        splits.append(Split(date.tz_localize(None).normalize(), ratio, "manual", note))
    if len({split.date for split in splits}) != len(splits):
        raise ValueError(f"Duplicate manual split dates for {ticker}.")
    return splits


def close_log_returns(prices: pd.DataFrame) -> pd.Series:
    close, volume = prices["Close"], prices["Volume"]
    valid = np.isfinite(close) & close.gt(0) & np.isfinite(volume) & volume.gt(0)
    return np.log(close.loc[valid]).diff()


def load_clean(
    ticker: str, *, raw: pd.DataFrame | None = None, actions: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Return cleaned OHLCV. Provenance and audit rows are in DataFrame.attrs."""
    ticker = ticker.strip().upper()
    filename = f"{ticker_filename(ticker)}.csv"
    prices = (read_raw_prices(ticker) if raw is None else raw).copy()
    required = [*OHLC, "Volume"]
    missing = set(required).difference(prices)
    if missing:
        raise ValueError(f"{ticker} is missing raw columns {', '.join(sorted(missing))}.")
    prices.index = normalize_dates(prices.index)
    prices = prices.loc[prices.index.notna() & ~prices.index.duplicated(keep="last")].sort_index()
    for name in required:
        prices[name] = pd.to_numeric(prices[name], errors="coerce").astype(float)

    audit = []

    def record(code, source, *, date=None, reference=None, ratio=None, log_return=None, detail=""):
        audit.append(dict(zip(ISSUE_COLUMNS, (
            ticker, date, code, source, reference, ratio, log_return, detail,
        ))))

    raw_returns = close_log_returns(prices)
    dates = raw_returns.index
    if actions is None:
        action_path = ROOT / "actions" / filename
        if action_path.is_file():
            actions = pd.read_csv(action_path).set_index("date")

    dividend_dates = pd.DatetimeIndex([])
    if actions is None:
        source = "ratio_fallback"
        adjusted = pd.to_numeric(prices.get("Adj Close", pd.Series(np.nan, index=prices.index)), errors="coerce")
        adjustment = (adjusted / prices["Close"]).reindex(dates)
        adjustment = adjustment.where(np.isfinite(adjustment) & adjustment.gt(0))
        jumps = adjustment.div(adjustment.shift())
        candidates = jumps.loc[jumps.sub(1).abs().gt(0.03) & np.isfinite(jumps)]
        splits = [Split(date, ratio, source) for date, ratio in candidates.items()]
        record("actions_source", source, detail="Yahoo actions file is missing. "
               "Adj Close/Close jumps over 3% are screened as unconfirmed split candidates.")
    else:
        source = "yahoo_actions"
        actions = actions.copy()
        actions.index = normalize_dates(actions.index)
        actions = actions.loc[actions.index.notna() & ~actions.index.duplicated(keep="last")]
        actions = actions.reindex(columns=ACTION_COLUMNS).apply(pd.to_numeric, errors="coerce")
        ratios = actions["Stock Splits"]
        ratios = ratios.loc[np.isfinite(ratios) & ratios.gt(0) & ratios.ne(1)]
        splits = [Split(date, ratio, source) for date, ratio in ratios.items()]
        dividend_dates = actions.index[actions["Dividends"].gt(0)]
        record("actions_source", source, detail="Yahoo action records supplied. "
               "Dividends leave price-return OHLC unchanged.")

    manual = manual_splits(ticker)
    if manual:
        session_of = dates.searchsorted
        splits = [
            split for split in splits
            if not any(
                override.date == split.date or (
                    abs(session_of(override.date) - session_of(split.date)) <= 7
                    and abs(np.log(override.ratio / split.ratio)) <= 0.05
                )
                for override in manual
            )
        ] + manual

    # Spike-and-reverse days (bad prints) must never be mistaken for a split break:
    # a large move followed within 2 sessions by an opposite move of similar size.
    spike_days = set()
    raw_values = raw_returns.to_numpy()
    for pos in range(1, len(raw_values)):
        if not np.isfinite(raw_values[pos]) or abs(raw_values[pos]) <= 0.15:
            continue
        for back in range(pos + 1, min(pos + 3, len(raw_values))):
            if (raw_values[pos] * raw_values[back] < 0
                    and abs(abs(raw_values[back]) / abs(raw_values[pos]) - 1) <= 0.30):
                spike_days.update(raw_returns.index[pos:back + 1])
                break

    price_factor = pd.Series(1.0, index=prices.index)
    protected = set()
    matched = set()
    selected = set()
    # An override gets first choice if two reports plausibly match the same trading session.
    for split in sorted(splits, key=lambda action: (action.source != "manual", action.date)):
        if prices.empty or not prices.index[0] <= split.date <= prices.index[-1]:
            record("split_outside_prices", split.source, date=split.date, ratio=split.ratio,
                   detail="Reported date falls outside the price history.")
            continue
        anchor = int(dates.searchsorted(split.date))
        window = raw_returns.iloc[max(0, anchor - 7):anchor + 3].drop(
            index=list(selected | spike_days), errors="ignore")
        expected = -np.log(split.ratio)
        # A credible match changes price in the direction implied by the split.
        errors = (window - expected).abs().where(window.mul(expected).gt(0)).dropna()
        found = not errors.empty and errors.min() <= SPLIT_TOLERANCE
        actual_date = errors.idxmin() if found else split.date
        observed = raw_returns.get(actual_date, np.nan)
        if split.source == "ratio_fallback" and (not found or abs(observed) <= LARGE_MOVE):
            record("split_candidate_unconfirmed", split.source, date=split.date,
                   reference=actual_date if found else None, ratio=split.ratio, log_return=observed,
                   detail="Ratio jump can include cash dividends. Applying an inferred split "
                          "requires a matching raw close move above 0.20 in absolute log units.")
            continue
        if split.source == "yahoo_actions" and not found:
            # Yahoo's Close is already split-adjusted at its own date. No raw break remains,
            # so applying the ratio again would double-adjust and create a fake jump.
            record("split_already_adjusted", split.source, date=split.date, ratio=split.ratio,
                   detail="No matching break in raw Close; Yahoo Close already reflects this split.")
            continue

        selected.add(actual_date)
        price_factor.loc[prices.index < actual_date] /= split.ratio
        protected.update((anchor, int(dates.searchsorted(actual_date))))
        if found:
            matched.add(actual_date)
        code = "split_date_unmatched" if not found else (
            "split_date_realigned" if actual_date != split.date else "split_adjusted"
        )
        record(code, split.source, date=actual_date, reference=split.date, ratio=split.ratio,
               log_return=observed, detail=split.note or (
                   "Applied at the reported date. No trading session matched within 0.05 log return."
                   if not found else "Back-adjusted prior OHLC and applied the inverse factor to volume."
               ))

    prices[list(OHLC)] = prices[list(OHLC)].mul(price_factor, axis=0)
    prices["Volume"] = prices["Volume"].div(price_factor)
    prices = prices.rename(columns={"Adj Close": "Yahoo Adj Close"})
    prices["Price Factor"] = price_factor
    prices["Adjustment Source"] = source + ("+manual" if manual else "")
    dividend_sessions = set(dividend_dates.intersection(prices.index))
    for date in sorted(dividend_sessions):
        record("dividend_price_return", source, date=date, detail="Cash dividend retained in price returns.")

    returns = close_log_returns(prices)
    values = returns.to_numpy()
    pos = 1
    while pos < len(values):
        if abs(values[pos]) <= 0.15 or not np.isfinite(values[pos]):
            pos += 1
            continue
        for recovery in range(pos + 1, min(pos + 3, len(values))):
            near_split = any(pos - 2 <= action_pos <= recovery + 2 for action_pos in protected)
            reverse = values[pos] * values[recovery] < 0
            similar = abs(abs(values[recovery]) / abs(values[pos]) - 1) <= 0.30
            would_drop_dividend = any(date in dividend_sessions for date in returns.index[pos:recovery])
            if near_split or would_drop_dividend or not (reverse and similar):
                continue
            for date in returns.index[pos:recovery]:
                record("bad_print_reversal", "close_returns", date=date, reference=returns.index[recovery],
                       log_return=returns.loc[date], detail="Price set to NaN. Recovery session retained.")
                prices.loc[date, list(OHLC)] = np.nan
            pos = recovery
            break
        pos += 1

    remaining = close_log_returns(prices)
    for date, value in remaining.loc[remaining.abs().gt(LARGE_MOVE)].items():
        if date not in matched:
            record("large_move_unexplained", "close_returns", date=date,
                   log_return=value, detail="Retained for review.")

    codes = {}
    for issue in audit:
        date = issue["date"]
        if date is not None:
            codes.setdefault(date, []).append(issue["reason_code"])
    prices["Reason Codes"] = pd.Series(
        {date: "|".join(dict.fromkeys(names)) for date, names in codes.items()}, dtype=str,
    ).reindex(prices.index).fillna("")
    prices.attrs["issues"] = audit
    prices.attrs["adjustment_source"] = source
    return prices


def main() -> int:
    cleaned_dir, results_dir = ROOT / "cleaned", ROOT / "results"
    cleaned_dir.mkdir(exist_ok=True)
    results_dir.mkdir(exist_ok=True)
    issues = []
    failed = False
    for ticker in read_tickers():
        try:
            prices = load_clean(ticker)
        except (OSError, ValueError, KeyError) as error:
            issues.append({"ticker": ticker, "reason_code": "cleaning_failed", "detail": str(error)})
            print(f"{ticker} {error}")
            failed = True
            continue
        prices.to_csv(cleaned_dir / f"{ticker_filename(ticker)}.csv")
        audit = prices.attrs["issues"]
        issues.extend(audit)
        counts = pd.Series([row["reason_code"] for row in audit]).value_counts().to_dict()
        print(f"{ticker} {prices.attrs['adjustment_source']} {counts}")
    pd.DataFrame(issues, columns=ISSUE_COLUMNS).to_csv(results_dir / "data_issues.csv", index=False)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
