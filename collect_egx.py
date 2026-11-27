"""Download daily EGX price history from Yahoo Finance and report data quality.
Usage:  python collect_egx.py            (reads tickers.txt, writes prices/*.csv + quality_report.csv)
Re-run any time: it re-downloads full history, so it doubles as the daily updater."""
import sys, pathlib, datetime as dt
import pandas as pd, yfinance as yf

here = pathlib.Path(__file__).parent
out = here / "prices"; out.mkdir(exist_ok=True)
tickers = [l.strip() for l in (here / "tickers.txt").read_text().splitlines() if l.strip() and not l.startswith("#")]
rows = []
for t in tickers:
    d = yf.download(t, period="max", auto_adjust=False, progress=False, multi_level_index=False)
    if d.empty:
        rows.append({"ticker": t, "rows": 0}); print(t, "NO DATA"); continue
    d.index.name = "date"
    d["downloaded_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    d.to_csv(out / f"{t.replace('.', '_')}.csv")
    gaps = d.index.to_series().diff().dt.days
    rows.append({"ticker": t, "rows": len(d), "first": d.index.min().date(), "last": d.index.max().date(),
                 "zero_volume_days": int((d["Volume"] == 0).sum()),
                 "gaps_over_7_days": int((gaps > 7).sum()),
                 "max_gap_days": int(gaps.max() or 0),
                 "flat_price_days": int((d["Close"].diff() == 0).sum())})
    print(rows[-1])
pd.DataFrame(rows).to_csv(here / "quality_report.csv", index=False)
print("saved to", out)
