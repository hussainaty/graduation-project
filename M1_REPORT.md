# EGX Risk Radar: M1 Progress Report

**Graduation project: stock-market AI for the Egyptian Exchange (EGX)**
**Status:** M1 (price-only model) complete · **Date:** 27 November 2026
**GitHub:** https://github.com/hussainaty/graduation-project

---

## 1. What M1 does

M1 forecasts **how much a stock will move** (the size of the move, up or down) over the next **1, 5 and 20 trading days**. It also gives a **90% range** for each forecast.

It does not predict whether the price goes up or down. It measures **risk**: how big tomorrow's move is likely to be. Risk managers, payment companies and investors care about this, and the research shows it can be predicted far more reliably than direction.

Target: the absolute log return `|log(P[t+h] / P[t])|` for h = 1, 5 and 20.

## 2. The paper we build on

- **Base paper:** Brini (2026), *arXiv:2607.05291*. It combines IBM's TTM time-series foundation model with the classic Log-HAR volatility model.
- **What the professor asked for:** take a recent paper and improve on it, using price data only (no news) as the first step.
- **What we add:**
  1. We test the paper on a new market, the **Egyptian EGX30**. It is an emerging market with a ±20% daily price limit and messy public data.
  2. We compare it against **16 models**, not just the paper's set.
  3. We add **adaptive conformal ranges** (Gibbs & Candès, 2021). They keep 90% coverage when the market changes, where standard ranges fall below 90%.
  4. We build an **automatic cleaning step** for the errors in free EGX data.

## 3. Data used

| Item | Detail |
|---|---|
| Source | Yahoo Finance (free), daily open, high, low, close and volume, plus dividends and splits |
| Stocks | **28 of the EGX30** (current list, 26 Nov 2026) |
| History | Up to 2002, where available. Models use **2013 onward**, about **88,000 stock-days** |
| Training | 2013–2021. The last 20% of this period calibrates the ranges |
| Testing | **2022 to Nov 2026**, about **1,150 trading days per stock**. The models never see this data during training |
| Updates | GitHub Actions downloads new prices and reruns everything each trading day at 15:00 UTC |

**Stocks used:** ABUK, ADIB, ALCN, AMOC, BTFH, CCAP, CLHO, COMI, EAST, EFID, EGAL, EMFD, ETEL, FWRY, GBCO, HELI, HRHO, ISPH, JUFO, MCQE, MFPC, ORHD, PHDC, RAYA, RMDA, SKPC, SWDY, TMGH.

**Excluded, with reasons:**

| Stock | Reason |
|---|---|
| VLMR, VLMRA | No data on Yahoo |
| ORAS | Zero trading volume on 97% of days |
| EFIH | Listed Oct 2021, so no data in the training period |

SWDY comes from our first 8-stock pilot and is no longer in the EGX30.

### Data cleaning

Free EGX data contains errors that would corrupt every model. The cleaner (`clean_prices.py`) logs every change it makes in `results/data_issues.csv`:

- **Splits Yahoo dated late:** 23 cases moved to the correct date. One example is the ADIB and EFID 2-for-1 split on 26 May 2025, which Yahoo recorded 11 days late.
- **Bad prints:** 149 one-day spikes that reverse the next day were removed.
- **Unrecorded corporate actions:** 13 moves too large to be real trading, since anything beyond the ±20% limit is impossible. Example: MFPC on 2 Jan 2024. Earlier prices were rescaled to match. **These still need checking against EGX disclosures.**

## 4. Models compared (16)

| Family | Models |
|---|---|
| Baseline | Naive (last observed move) |
| HAR family | HAR, Log-HAR, LHAR (leverage), HAR-RV, HAR-RANGE (high/low range), HAR-X (volume, overnight gap, market volatility) |
| GARCH family | GARCH, GJR-GARCH, EGARCH (Student-t errors) |
| Hybrid | HAR-GARCH |
| Combinations | Equal-weight, inverse-MSE, ridge stacking |
| AI foundation model | IBM TTM (`granite-timeseries-ttm-r2`, used without retraining) |
| **Paper's method** | **TTM + Log-HAR** (equal-weight average) |

**How we score them:**
- Mean absolute error (MAE) on the 2022–2026 test period, with every model scored on the same days.
- The **Diebold–Mariano test** (Newey-West variance) checks whether each model is significantly better or worse than HAR at the 5% level.

## 5. Results

### Accuracy (lower rank is better; ranks averaged over 27–28 stocks)

| Horizon | Best model | Average rank | Stocks where it is significantly better than HAR | Stocks where it is significantly worse | Second best |
|---|---|---|---|---|---|
| 1 day | **TTM + Log-HAR** | **1.44** | **14 / 27** | 0 | HAR (4.21) |
| 5 days | **TTM + Log-HAR** | **1.59** | **17 / 27** | 1 | HAR (6.43) |
| 20 days | **TTM + Log-HAR** | **4.41** | 8 / 27 | 2 | EGARCH (5.21) |

TTM runs on 27 stocks. RMDA listed in 2019 and doesn't have the 512 days of history TTM needs.

### Range reliability (target: 90%)

| Horizon | Standard conformal range | **Adaptive conformal range** |
|---|---|---|
| 1 day | 85.4% | **90.0%** |
| 5 days | 86.0% | **90.2%** |
| 20 days | 85.1% | **90.0%** |

### Key findings

1. **The paper's method holds up in Egypt.** TTM + Log-HAR is the best model at every horizon and significantly beats HAR on half or more of the EGX30 stocks at 1 and 5 days.
2. **The AI model alone is not enough.** TTM by itself ranks near the bottom. It only works when combined with the classic model.
3. **Adding more inputs does not help.** Volume and overnight gaps (HAR-X) make forecasts worse.
4. **GARCH models catch up at 20 days.** EGARCH comes second at the monthly horizon.
5. **Our contribution:** adaptive ranges keep their promised 90% coverage. Standard ranges miss it by about 5 points, so they understate risk.

> **One-line summary:** On 27 EGX30 stocks, the TTM + Log-HAR method from Brini (2026) significantly beats the HAR baseline on 14 stocks at 1 day and 17 at 5 days. Our adaptive ranges keep 90% coverage where standard ranges drop to about 85%.

## 6. What was built

| File | Purpose |
|---|---|
| `collect_egx.py` | Downloads prices, dividends and splits for every ticker in `tickers.txt` |
| `clean_prices.py` | Fixes splits, bad prints and corporate actions, and logs every change |
| `m1_har.py` | Main experiment: trains all 16 models, tests them and writes results |
| `m1_garch.py`, `m1_ttm.py`, `m1_evaluation.py` | GARCH family, IBM TTM, and the statistical tests |
| `app.py` | **Demo app** (Streamlit): pick any EGX stock and see its forecasts and 90% ranges |
| `.github/workflows/collect.yml` | Runs automatically every trading day |
| `results/` | `m1_summary.csv`, `m1_results.csv` (per stock), forecasts, `data_issues.csv` |

**Run it yourself:**
```
git clone https://github.com/hussainaty/graduation-project.git
cd graduation-project
pip install -r requirements.txt
streamlit run app.py
```

TTM needs one more install step; see the comment in `requirements.txt`. Without it, the other models still run.

Cost: **0 EGP**. All tools are free: Yahoo data, GitHub Actions, open-source models.

## 7. Next steps (open for team members)

1. **Data check (finance):** confirm the 13 inferred corporate actions against EGX disclosures, and record confirmed ones in `corporate_actions_manual.csv`.
2. **Literature review:** Brini (2026) plus related HAR, TTM and conformal prediction papers.
3. **M2, news model:** collect dated Arabic and English news headlines for the 28 stocks.
4. **M4, earnings model:** collect quarterly earnings dates and results.
5. **M3, combined model:** prices plus news, once M2 data exists.
6. **Demo and pitch:** polish the app and prepare the Fawry presentation.
7. **Thesis chapters:** methodology and results for M1.
