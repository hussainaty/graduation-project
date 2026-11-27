# M1 results

The backtest forecasts absolute cleaned-close log returns for 1, 5, and 20 retained sessions.
Average MAE rank gives each ticker equal weight within a horizon. Rank 1 is best.
Diebold–Mariano counts use paired absolute errors, a two-sided 5% threshold, and Newey–West variance with h−1 lags. The p-values are unadjusted for multiple comparisons.

## Model rankings

| Sessions | Model | Avg. MAE rank | Mean MAE | Tickers | Significant wins vs HAR | Significant losses vs HAR |
|---:|---|---:|---:|---:|---:|---:|
| 1 | TTM+Log-HAR | 1.50 | 1.16% | 8 | 4 | 0 |
| 1 | HAR | 4.25 | 1.18% | 8 | 0 | 0 |
| 1 | Log-HAR | 4.50 | 1.18% | 8 | 1 | 0 |
| 1 | LHAR | 4.75 | 1.18% | 8 | 0 | 0 |
| 1 | HAR-X | 6.00 | 1.19% | 8 | 0 | 2 |
| 1 | Combo Ridge | 6.25 | 1.19% | 8 | 2 | 3 |
| 1 | HAR-RV | 6.88 | 1.19% | 8 | 0 | 1 |
| 1 | Combo Inv-MSE | 7.88 | 1.20% | 8 | 0 | 5 |
| 1 | Combo Equal | 8.62 | 1.20% | 8 | 0 | 5 |
| 1 | HAR-RANGE | 9.88 | 1.22% | 8 | 0 | 5 |
| 1 | HAR-GARCH | 10.25 | 1.21% | 8 | 0 | 6 |
| 1 | TTM | 11.38 | 1.21% | 8 | 0 | 3 |
| 1 | EGARCH | 12.62 | 1.25% | 8 | 0 | 8 |
| 1 | Naive | 13.00 | 1.23% | 8 | 0 | 7 |
| 1 | GJR-GARCH | 13.88 | 1.25% | 8 | 0 | 8 |
| 1 | GARCH | 14.38 | 1.25% | 8 | 0 | 8 |
| 5 | TTM+Log-HAR | 1.25 | 2.72% | 8 | 5 | 0 |
| 5 | EGARCH | 6.62 | 2.84% | 8 | 3 | 3 |
| 5 | Combo Inv-MSE | 6.88 | 2.83% | 8 | 4 | 2 |
| 5 | HAR | 6.88 | 2.83% | 8 | 0 | 0 |
| 5 | Combo Equal | 7.12 | 2.83% | 8 | 4 | 2 |
| 5 | Log-HAR | 7.12 | 2.83% | 8 | 1 | 1 |
| 5 | LHAR | 7.88 | 2.84% | 8 | 0 | 0 |
| 5 | Naive | 8.50 | 2.83% | 8 | 1 | 1 |
| 5 | GJR-GARCH | 8.88 | 2.87% | 8 | 1 | 3 |
| 5 | GARCH | 9.25 | 2.87% | 8 | 1 | 4 |
| 5 | HAR-RANGE | 9.50 | 2.85% | 8 | 0 | 3 |
| 5 | HAR-X | 9.50 | 2.86% | 8 | 0 | 2 |
| 5 | HAR-RV | 9.75 | 2.85% | 8 | 0 | 1 |
| 5 | TTM | 11.50 | 2.87% | 8 | 1 | 1 |
| 5 | Combo Ridge | 12.00 | 2.93% | 8 | 1 | 3 |
| 5 | HAR-GARCH | 13.38 | 2.93% | 8 | 0 | 5 |
| 20 | TTM+Log-HAR | 4.12 | 5.75% | 8 | 1 | 0 |
| 20 | EGARCH | 4.12 | 5.86% | 8 | 2 | 1 |
| 20 | GARCH | 6.00 | 5.99% | 8 | 3 | 2 |
| 20 | GJR-GARCH | 6.88 | 5.98% | 8 | 3 | 2 |
| 20 | Combo Inv-MSE | 6.88 | 6.02% | 8 | 1 | 1 |
| 20 | Log-HAR | 7.00 | 6.02% | 8 | 2 | 0 |
| 20 | Combo Equal | 7.75 | 6.03% | 8 | 1 | 1 |
| 20 | HAR | 8.25 | 6.09% | 8 | 0 | 0 |
| 20 | LHAR | 8.50 | 6.09% | 8 | 3 | 0 |
| 20 | Naive | 8.75 | 5.94% | 8 | 1 | 0 |
| 20 | HAR-X | 8.75 | 6.12% | 8 | 0 | 2 |
| 20 | HAR-RV | 9.88 | 6.18% | 8 | 0 | 1 |
| 20 | TTM | 10.00 | 6.12% | 8 | 1 | 2 |
| 20 | Combo Ridge | 12.88 | 6.44% | 8 | 0 | 2 |
| 20 | HAR-RANGE | 13.12 | 6.30% | 8 | 1 | 3 |
| 20 | HAR-GARCH | 13.12 | 6.44% | 8 | 0 | 5 |

## What performed best

- TTM+Log-HAR had the lowest average rank at 1 session (1.50).
- TTM+Log-HAR had the lowest average rank at 5 sessions (1.25).
- TTM+Log-HAR and EGARCH tied for the lowest average rank at 20 sessions (4.12).
- EGARCH ranked ahead of HAR at 2/3 horizons. Significant ticker comparisons at the 5% threshold were 1-session 0/8 wins and 8/8 losses, 5-session 3/8 wins and 3/8 losses, 20-session 2/8 wins and 1/8 losses.
- GARCH ranked ahead of HAR at 1/3 horizons. Significant ticker comparisons at the 5% threshold were 1-session 0/8 wins and 8/8 losses, 5-session 1/8 wins and 4/8 losses, 20-session 3/8 wins and 2/8 losses.
- GJR-GARCH ranked ahead of HAR at 1/3 horizons. Significant ticker comparisons at the 5% threshold were 1-session 0/8 wins and 8/8 losses, 5-session 1/8 wins and 3/8 losses, 20-session 3/8 wins and 2/8 losses.
- HAR-GARCH ranked ahead of HAR at 0/3 horizons. Significant ticker comparisons at the 5% threshold were 1-session 0/8 wins and 6/8 losses, 5-session 0/8 wins and 5/8 losses, 20-session 0/8 wins and 5/8 losses.
- HAR-X ranked ahead of HAR at 0/3 horizons. Significant ticker comparisons at the 5% threshold were 1-session 0/8 wins and 2/8 losses, 5-session 0/8 wins and 2/8 losses, 20-session 0/8 wins and 2/8 losses.

## Adaptive coverage

Each ticker and horizon chooses an individual model and a combination using pre-2022 validation MAE. The rows below compare both intervals on the same forecasts. TTM models are reported separately when available.
Adaptive updates use gamma 0.005 after the h-session outcome is observed.

| Sessions | Selected model type | Tickers | Standard coverage | Adaptive coverage | Unbounded adaptive share |
|---:|---|---:|---:|---:|---:|
| 1 | Combination | 8 | 83.2% | 90.0% | 0.2% |
| 1 | Individual | 8 | 84.6% | 90.0% | 0.3% |
| 1 | TTM | 8 | 85.3% | 90.0% | 0.1% |
| 1 | TTM+Log-HAR | 8 | 85.0% | 90.0% | 0.1% |
| 5 | Combination | 8 | 83.9% | 90.1% | 1.9% |
| 5 | Individual | 8 | 86.0% | 90.1% | 0.8% |
| 5 | TTM | 8 | 86.6% | 90.1% | 1.0% |
| 5 | TTM+Log-HAR | 8 | 86.5% | 90.1% | 1.0% |
| 20 | Combination | 8 | 81.3% | 89.4% | 18.1% |
| 20 | Individual | 8 | 84.6% | 89.9% | 11.9% |
| 20 | TTM | 8 | 85.9% | 90.2% | 9.3% |
| 20 | TTM+Log-HAR | 8 | 85.6% | 90.2% | 10.2% |

Across selected ticker and horizon pairs, mean coverage changed from 83.9% to 89.9%. 22/48 pairs reached 90% adaptive coverage. Unbounded intervals cover every move and are included in both coverage and mean width.

## Data cleaning

M1 uses split-adjusted Close and keeps cash-dividend moves as price returns. Reversal detection and the placement of reported splits use nearby historical sessions, so this is a retrospective clean of the price history.
The cleaned CSVs and data_issues.csv provide the event dates, source, and reasons.

| Ticker | Source | Split adjustments | Unconfirmed candidates | Reversal rows nulled | Large moves retained |
|---|---|---:|---:|---:|---:|
| COMI.CA | yahoo_actions | 1 | 0 | 0 | 1 |
| FWRY.CA | yahoo_actions | 0 | 0 | 0 | 0 |
| ETEL.CA | yahoo_actions | 0 | 0 | 2 | 1 |
| HRHO.CA | yahoo_actions | 0 | 0 | 6 | 7 |
| TMGH.CA | yahoo_actions | 1 | 0 | 0 | 1 |
| SWDY.CA | yahoo_actions | 1 | 0 | 5 | 1 |
| EAST.CA | yahoo_actions | 1 | 0 | 31 | 9 |
| ABUK.CA | yahoo_actions | 1 | 0 | 18 | 11 |

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
- FWRY.CA — Excluded 49 zero-volume rows since 2013-01-01.
- ETEL.CA — Excluded 0 invalid dates, 0 duplicate dates, and 1 other invalid price or volume rows.
- ETEL.CA — Excluded 195 zero-volume rows since 2013-01-01.
- HRHO.CA — Excluded 182 zero-volume rows since 2013-01-01.
- TMGH.CA — Excluded 195 zero-volume rows since 2013-01-01.
- SWDY.CA — Excluded 0 invalid dates, 0 duplicate dates, and 3 other invalid price or volume rows.
- SWDY.CA — Excluded 199 zero-volume rows since 2013-01-01.
- EAST.CA — Excluded 0 invalid dates, 0 duplicate dates, and 1 other invalid price or volume rows.
- EAST.CA — Excluded 294 zero-volume rows since 2013-01-01.
- ABUK.CA — Excluded 336 zero-volume rows since 2013-01-01.
