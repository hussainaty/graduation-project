# M1 results

The backtest forecasts absolute cleaned-close log returns for 1, 5, and 20 retained sessions.
Average MAE rank gives each ticker equal weight within a horizon. Rank 1 is best.
Diebold–Mariano counts use paired absolute errors, a two-sided 5% threshold, and Newey–West variance with h−1 lags. The p-values are unadjusted for multiple comparisons.

## Model rankings

| Sessions | Model | Avg. MAE rank | Mean MAE | Tickers | Significant wins vs HAR | Significant losses vs HAR |
|---:|---|---:|---:|---:|---:|---:|
| 1 | TTM+Log-HAR | 1.44 | 1.29% | 27 | 14 | 0 |
| 1 | HAR | 4.21 | 1.32% | 28 | 0 | 0 |
| 1 | LHAR | 4.61 | 1.32% | 28 | 0 | 3 |
| 1 | Log-HAR | 4.86 | 1.33% | 28 | 1 | 3 |
| 1 | HAR-X | 5.96 | 1.33% | 28 | 0 | 9 |
| 1 | HAR-RV | 6.93 | 1.33% | 28 | 2 | 9 |
| 1 | Combo Ridge | 7.57 | 1.35% | 28 | 5 | 11 |
| 1 | Combo Inv-MSE | 7.86 | 1.34% | 28 | 0 | 19 |
| 1 | Combo Equal | 8.75 | 1.34% | 28 | 0 | 20 |
| 1 | HAR-GARCH | 8.75 | 1.35% | 28 | 0 | 17 |
| 1 | TTM | 10.19 | 1.35% | 27 | 1 | 10 |
| 1 | HAR-RANGE | 11.46 | 1.38% | 28 | 0 | 18 |
| 1 | Naive | 12.11 | 1.37% | 28 | 0 | 21 |
| 1 | EGARCH | 12.50 | 1.39% | 28 | 0 | 26 |
| 1 | GJR-GARCH | 13.86 | 1.40% | 28 | 0 | 28 |
| 1 | GARCH | 14.25 | 1.41% | 28 | 0 | 28 |
| 5 | TTM+Log-HAR | 1.59 | 3.03% | 27 | 17 | 1 |
| 5 | HAR | 6.43 | 3.15% | 28 | 0 | 0 |
| 5 | Log-HAR | 6.89 | 3.15% | 28 | 3 | 2 |
| 5 | Naive | 7.00 | 3.13% | 28 | 5 | 2 |
| 5 | LHAR | 7.04 | 3.16% | 28 | 1 | 4 |
| 5 | EGARCH | 7.36 | 3.18% | 28 | 9 | 10 |
| 5 | Combo Inv-MSE | 7.75 | 3.17% | 28 | 8 | 8 |
| 5 | Combo Equal | 8.29 | 3.17% | 28 | 8 | 8 |
| 5 | HAR-RV | 8.75 | 3.18% | 28 | 2 | 7 |
| 5 | HAR-X | 9.14 | 3.18% | 28 | 0 | 5 |
| 5 | GJR-GARCH | 9.61 | 3.22% | 28 | 6 | 15 |
| 5 | GARCH | 9.93 | 3.23% | 28 | 5 | 16 |
| 5 | TTM | 10.70 | 3.22% | 27 | 2 | 4 |
| 5 | HAR-RANGE | 11.54 | 3.29% | 28 | 0 | 15 |
| 5 | Combo Ridge | 11.61 | 3.36% | 28 | 2 | 14 |
| 5 | HAR-GARCH | 11.71 | 3.29% | 28 | 2 | 17 |
| 20 | TTM+Log-HAR | 4.41 | 6.38% | 27 | 8 | 2 |
| 20 | EGARCH | 5.21 | 6.52% | 28 | 7 | 4 |
| 20 | Log-HAR | 7.07 | 6.67% | 28 | 3 | 1 |
| 20 | GARCH | 7.21 | 6.71% | 28 | 8 | 5 |
| 20 | GJR-GARCH | 7.29 | 6.70% | 28 | 7 | 5 |
| 20 | Combo Inv-MSE | 7.54 | 6.65% | 28 | 7 | 2 |
| 20 | Naive | 7.93 | 6.56% | 28 | 5 | 2 |
| 20 | HAR | 8.11 | 6.69% | 28 | 0 | 0 |
| 20 | Combo Equal | 8.14 | 6.66% | 28 | 7 | 3 |
| 20 | LHAR | 8.46 | 6.69% | 28 | 2 | 4 |
| 20 | HAR-RV | 8.96 | 6.73% | 28 | 3 | 2 |
| 20 | HAR-X | 9.11 | 6.71% | 28 | 0 | 7 |
| 20 | Combo Ridge | 10.93 | 7.24% | 28 | 1 | 6 |
| 20 | TTM | 11.22 | 6.88% | 27 | 3 | 6 |
| 20 | HAR-GARCH | 11.68 | 6.97% | 28 | 2 | 14 |
| 20 | HAR-RANGE | 12.18 | 6.96% | 28 | 2 | 11 |

## What performed best

- TTM+Log-HAR had the lowest average rank at 1 session (1.44).
- TTM+Log-HAR had the lowest average rank at 5 sessions (1.59).
- TTM+Log-HAR had the lowest average rank at 20 sessions (4.41).
- EGARCH ranked ahead of HAR at 1/3 horizons. Significant ticker comparisons at the 5% threshold were 1-session 0/28 wins and 26/28 losses, 5-session 9/28 wins and 10/28 losses, 20-session 7/28 wins and 4/28 losses.
- GARCH ranked ahead of HAR at 1/3 horizons. Significant ticker comparisons at the 5% threshold were 1-session 0/28 wins and 28/28 losses, 5-session 5/28 wins and 16/28 losses, 20-session 8/28 wins and 5/28 losses.
- GJR-GARCH ranked ahead of HAR at 1/3 horizons. Significant ticker comparisons at the 5% threshold were 1-session 0/28 wins and 28/28 losses, 5-session 6/28 wins and 15/28 losses, 20-session 7/28 wins and 5/28 losses.
- HAR-GARCH ranked ahead of HAR at 0/3 horizons. Significant ticker comparisons at the 5% threshold were 1-session 0/28 wins and 17/28 losses, 5-session 2/28 wins and 17/28 losses, 20-session 2/28 wins and 14/28 losses.
- HAR-X ranked ahead of HAR at 0/3 horizons. Significant ticker comparisons at the 5% threshold were 1-session 0/28 wins and 9/28 losses, 5-session 0/28 wins and 5/28 losses, 20-session 0/28 wins and 7/28 losses.

## Adaptive coverage

Each ticker and horizon chooses an individual model and a combination using pre-2022 validation MAE. The rows below compare both intervals on the same forecasts. TTM models are reported separately when available.
Adaptive updates use gamma 0.005 after the h-session outcome is observed.

| Sessions | Selected model type | Tickers | Standard coverage | Adaptive coverage | Unbounded adaptive share |
|---:|---|---:|---:|---:|---:|
| 1 | Combination | 28 | 85.0% | 90.0% | 0.2% |
| 1 | Individual | 28 | 86.0% | 90.1% | 0.1% |
| 1 | TTM | 27 | 86.6% | 90.0% | 0.1% |
| 1 | TTM+Log-HAR | 27 | 86.2% | 90.0% | 0.1% |
| 5 | Combination | 28 | 84.3% | 90.1% | 2.6% |
| 5 | Individual | 28 | 86.3% | 90.3% | 0.9% |
| 5 | TTM | 27 | 87.4% | 90.3% | 1.5% |
| 5 | TTM+Log-HAR | 27 | 87.0% | 90.2% | 1.5% |
| 20 | Combination | 28 | 83.9% | 89.9% | 14.6% |
| 20 | Individual | 28 | 84.9% | 90.0% | 11.0% |
| 20 | TTM | 27 | 86.4% | 90.1% | 9.7% |
| 20 | TTM+Log-HAR | 27 | 85.7% | 90.0% | 10.0% |

Across selected ticker and horizon pairs, mean coverage changed from 85.1% to 90.1%. 77/168 pairs reached 90% adaptive coverage. Unbounded intervals cover every move and are included in both coverage and mean width.

## Data cleaning

M1 uses split-adjusted Close and keeps cash-dividend moves as price returns. Reversal detection and the placement of reported splits use nearby historical sessions, so this is a retrospective clean of the price history.
The cleaned CSVs and data_issues.csv provide the event dates, source, and reasons.

| Ticker | Source | Split adjustments | Unconfirmed candidates | Reversal rows nulled | Large moves retained |
|---|---|---:|---:|---:|---:|
| COMI.CA | yahoo_actions | 1 | 0 | 0 | 1 |
| HRHO.CA | yahoo_actions | 1 | 0 | 6 | 7 |
| TMGH.CA | yahoo_actions | 1 | 0 | 0 | 1 |
| CCAP.CA | yahoo_actions | 0 | 0 | 0 | 1 |
| ETEL.CA | yahoo_actions | 0 | 0 | 2 | 1 |
| AMOC.CA | yahoo_actions | 0 | 0 | 1 | 1 |
| EGAL.CA | yahoo_actions | 1 | 0 | 7 | 7 |
| BTFH.CA | yahoo_actions | 1 | 0 | 1 | 1 |
| GBCO.CA | yahoo_actions | 0 | 0 | 1 | 3 |
| HELI.CA | yahoo_actions | 1 | 0 | 1 | 6 |
| EFID.CA | yahoo_actions | 2 | 0 | 0 | 0 |
| ISPH.CA | yahoo_actions | 1 | 0 | 0 | 0 |
| ORHD.CA | yahoo_actions | 1 | 0 | 2 | 5 |
| RAYA.CA | yahoo_actions | 2 | 0 | 0 | 3 |
| PHDC.CA | yahoo_actions | 1 | 0 | 0 | 4 |
| SKPC.CA | yahoo_actions | 2 | 0 | 0 | 3 |
| ABUK.CA | yahoo_actions | 1 | 0 | 18 | 10 |
| EAST.CA | yahoo_actions | 1 | 0 | 31 | 7 |
| CLHO.CA | yahoo_actions | 0 | 0 | 0 | 0 |
| MFPC.CA | yahoo_actions | 1 | 0 | 1 | 1 |
| JUFO.CA | yahoo_actions | 2 | 0 | 0 | 0 |
| FWRY.CA | yahoo_actions | 0 | 0 | 0 | 0 |
| EMFD.CA | yahoo_actions | 0 | 0 | 0 | 0 |
| ADIB.CA | yahoo_actions | 1 | 0 | 47 | 7 |
| MCQE.CA | yahoo_actions | 0 | 0 | 26 | 10 |
| RMDA.CA | yahoo_actions | 1 | 0 | 0 | 0 |
| ALCN.CA | yahoo_actions | 1 | 0 | 0 | 7 |
| SWDY.CA | yahoo_actions | 1 | 0 | 5 | 1 |

### EAST.CA and ABUK.CA before and after

The baseline is the previous Yahoo Adj Close model. Maximum daily moves use retained sessions from 2013 onward. The comparison CSV gives MAE and observation counts for each horizon and captures Student-t nu before any Gaussian refit.

| Ticker | Max abs log return before | After | GARCH nu before → after | EGARCH nu before → after |
|---|---:|---:|---:|---:|
| ABUK.CA | 22.13% | 22.13% | 2.903 (Gaussian refit) → 2.839 (Gaussian refit) | 2.050 (Gaussian refit) → 2.050 (Gaussian refit) |
| EAST.CA | 40.68% | 14.50% | 2.505 (Gaussian refit) → 2.470 (Gaussian refit) | 2.050 (Gaussian refit) → 2.050 (Gaussian refit) |

| Ticker | Model | MAE before → after at 1 session | At 5 sessions | At 20 sessions |
|---|---|---:|---:|---:|
| ABUK.CA | EGARCH | 1.248% → 1.265% | 2.929% → 2.962% | 6.261% → 6.019% |
| ABUK.CA | GARCH | 1.260% → 1.275% | 2.984% → 3.017% | 6.368% → 6.092% |
| ABUK.CA | HAR | 1.185% → 1.195% | 2.847% → 2.893% | 6.783% → 6.504% |
| ABUK.CA | Log-HAR | 1.170% → 1.182% | 2.840% → 2.868% | 6.353% → 6.082% |
| EAST.CA | EGARCH | 1.423% → 1.315% | 3.141% → 2.745% | 6.088% → 5.358% |
| EAST.CA | GARCH | 1.485% → 1.323% | 3.401% → 2.756% | 7.309% → 5.401% |
| EAST.CA | HAR | 1.326% → 1.267% | 2.886% → 2.721% | 5.899% → 5.538% |
| EAST.CA | Log-HAR | 1.280% → 1.256% | 2.858% → 2.718% | 5.935% → 5.442% |

## TTM comparison

TTM uses the frozen IBM Granite checkpoint and a 512-session trailing window per origin. TTM+Log-HAR averages its point forecasts with Log-HAR. Each available model receives standard and adaptive ranges and a paired Diebold?Mariano comparison against HAR.
TTM models were scored where enough forecast and calibration history was available.

## Data and model notes

- Forecast CSVs retain the standard HAR backtest and the original six columns.
- A three-member combination uses HAR, LHAR, and HAR-RANGE when a GJR-GARCH forecast is unavailable.
- HARQ was skipped because daily OHLCV cannot estimate intraday quarticity. A single daily return to the fourth power simply squares the daily variance proxy.
- COMI.CA — Excluded 158 zero-volume rows since 2013-01-01.
- HRHO.CA — Excluded 182 zero-volume rows since 2013-01-01.
- TMGH.CA — Excluded 195 zero-volume rows since 2013-01-01.
- CCAP.CA — Excluded 180 zero-volume rows since 2013-01-01.
- ETEL.CA — Excluded 0 invalid dates, 0 duplicate dates, and 1 other invalid price or volume rows.
- ETEL.CA — Excluded 195 zero-volume rows since 2013-01-01.
- AMOC.CA — Excluded 184 zero-volume rows since 2013-01-01.
- EGAL.CA — Excluded 335 zero-volume rows since 2013-01-01.
- BTFH.CA — Excluded 0 invalid dates, 0 duplicate dates, and 1 other invalid price or volume rows.
- BTFH.CA — Excluded 455 zero-volume rows since 2013-01-01.
- GBCO.CA — Excluded 283 zero-volume rows since 2013-01-01.
- HELI.CA — Excluded 200 zero-volume rows since 2013-01-01.
- EFID.CA — Excluded 364 zero-volume rows since 2013-01-01.
- ISPH.CA — Excluded 96 zero-volume rows since 2013-01-01.
- ORHD.CA — Excluded 716 zero-volume rows since 2013-01-01.
- RAYA.CA — Excluded 636 zero-volume rows since 2013-01-01.
- PHDC.CA — Excluded 200 zero-volume rows since 2013-01-01.
- SKPC.CA — Excluded 160 zero-volume rows since 2013-01-01.
- ABUK.CA — Excluded 336 zero-volume rows since 2013-01-01.
- EAST.CA — Excluded 0 invalid dates, 0 duplicate dates, and 1 other invalid price or volume rows.
- EAST.CA — Excluded 294 zero-volume rows since 2013-01-01.
- CLHO.CA — Excluded 121 zero-volume rows since 2013-01-01.
- MFPC.CA — Excluded 0 invalid dates, 0 duplicate dates, and 1 other invalid price or volume rows.
- MFPC.CA — Excluded 126 zero-volume rows since 2013-01-01.
- JUFO.CA — Excluded 230 zero-volume rows since 2013-01-01.
- FWRY.CA — Excluded 49 zero-volume rows since 2013-01-01.
- EMFD.CA — Excluded 176 zero-volume rows since 2013-01-01.
- ADIB.CA — Excluded 169 zero-volume rows since 2013-01-01.
- MCQE.CA — Excluded 0 invalid dates, 0 duplicate dates, and 2 other invalid price or volume rows.
- MCQE.CA — Excluded 255 zero-volume rows since 2013-01-01.
- RMDA.CA — Excluded 55 zero-volume rows since 2013-01-01.
- ALCN.CA — Excluded 243 zero-volume rows since 2013-01-01.
- SWDY.CA — Excluded 0 invalid dates, 0 duplicate dates, and 3 other invalid price or volume rows.
- SWDY.CA — Excluded 199 zero-volume rows since 2013-01-01.
- RMDA.CA — TTM has too few held-out conformal residuals at horizon 1.
- RMDA.CA — TTM+Log-HAR has too few held-out conformal residuals at horizon 1.
- RMDA.CA — TTM has too few held-out conformal residuals at horizon 5.
- RMDA.CA — TTM+Log-HAR has too few held-out conformal residuals at horizon 5.
- RMDA.CA — TTM has too few held-out conformal residuals at horizon 20.
- RMDA.CA — TTM+Log-HAR has too few held-out conformal residuals at horizon 20.
