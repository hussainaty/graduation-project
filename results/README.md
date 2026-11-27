# M1 results

The backtest forecasts absolute adjusted-close log returns for 1, 5, and 20 retained sessions.
Average MAE rank gives each ticker equal weight within a horizon. Rank 1 is best.
Diebold–Mariano counts use paired absolute errors, a two-sided 5% threshold, and Newey–West variance with h−1 lags. The p-values are unadjusted for multiple comparisons.

## Model rankings

| Sessions | Model | Avg. MAE rank | Mean MAE | Tickers | Significant wins vs HAR | Significant losses vs HAR |
|---:|---|---:|---:|---:|---:|---:|
| 1 | Log-HAR | 3.50 | 1.19% | 8 | 2 | 0 |
| 1 | HAR | 3.75 | 1.20% | 8 | 0 | 0 |
| 1 | LHAR | 4.25 | 1.20% | 8 | 0 | 0 |
| 1 | Combo Ridge | 4.38 | 1.20% | 8 | 1 | 2 |
| 1 | HAR-X | 5.38 | 1.20% | 8 | 1 | 2 |
| 1 | HAR-RV | 5.38 | 1.20% | 8 | 0 | 1 |
| 1 | Combo Inv-MSE | 6.75 | 1.21% | 8 | 0 | 4 |
| 1 | Combo Equal | 7.38 | 1.21% | 8 | 0 | 4 |
| 1 | HAR-GARCH | 8.38 | 1.22% | 8 | 0 | 5 |
| 1 | HAR-RANGE | 8.50 | 1.23% | 8 | 0 | 4 |
| 1 | Naive | 10.75 | 1.24% | 8 | 0 | 5 |
| 1 | EGARCH | 11.25 | 1.26% | 8 | 0 | 8 |
| 1 | GJR-GARCH | 12.62 | 1.27% | 8 | 0 | 8 |
| 1 | GARCH | 12.75 | 1.28% | 8 | 0 | 8 |
| 5 | Combo Inv-MSE | 5.50 | 2.85% | 8 | 4 | 3 |
| 5 | Log-HAR | 5.75 | 2.85% | 8 | 1 | 1 |
| 5 | HAR | 5.75 | 2.85% | 8 | 0 | 0 |
| 5 | EGARCH | 5.88 | 2.88% | 8 | 3 | 3 |
| 5 | Combo Equal | 6.25 | 2.86% | 8 | 4 | 3 |
| 5 | LHAR | 6.50 | 2.86% | 8 | 0 | 0 |
| 5 | Naive | 7.00 | 2.85% | 8 | 1 | 1 |
| 5 | HAR-RANGE | 7.25 | 2.87% | 8 | 0 | 2 |
| 5 | HAR-RV | 7.75 | 2.86% | 8 | 1 | 1 |
| 5 | GJR-GARCH | 8.12 | 2.95% | 8 | 1 | 3 |
| 5 | GARCH | 8.62 | 2.96% | 8 | 1 | 4 |
| 5 | HAR-X | 8.75 | 2.88% | 8 | 0 | 3 |
| 5 | Combo Ridge | 9.88 | 2.94% | 8 | 1 | 3 |
| 5 | HAR-GARCH | 12.00 | 2.97% | 8 | 0 | 5 |
| 20 | EGARCH | 4.12 | 5.99% | 8 | 2 | 0 |
| 20 | GARCH | 5.88 | 6.26% | 8 | 1 | 3 |
| 20 | Naive | 6.00 | 6.02% | 8 | 1 | 0 |
| 20 | Log-HAR | 6.12 | 6.14% | 8 | 1 | 0 |
| 20 | Combo Inv-MSE | 6.50 | 6.14% | 8 | 2 | 0 |
| 20 | LHAR | 6.50 | 6.19% | 8 | 3 | 0 |
| 20 | Combo Equal | 6.62 | 6.14% | 8 | 2 | 0 |
| 20 | HAR | 7.00 | 6.20% | 8 | 0 | 0 |
| 20 | GJR-GARCH | 7.00 | 6.28% | 8 | 1 | 3 |
| 20 | HAR-X | 7.62 | 6.22% | 8 | 0 | 2 |
| 20 | HAR-RV | 8.12 | 6.28% | 8 | 0 | 2 |
| 20 | Combo Ridge | 10.88 | 6.58% | 8 | 0 | 3 |
| 20 | HAR-RANGE | 11.00 | 6.46% | 8 | 1 | 3 |
| 20 | HAR-GARCH | 11.62 | 6.50% | 8 | 0 | 5 |

## What performed best

- Log-HAR had the lowest average rank at 1 session (3.50).
- Combo Inv-MSE had the lowest average rank at 5 sessions (5.50).
- EGARCH had the lowest average rank at 20 sessions (4.12).
- EGARCH ranked ahead of HAR at 1/3 horizons. Significant ticker comparisons at the 5% threshold were 1-session 0/8 wins and 8/8 losses, 5-session 3/8 wins and 3/8 losses, 20-session 2/8 wins and 0/8 losses.
- GARCH ranked ahead of HAR at 1/3 horizons. Significant ticker comparisons at the 5% threshold were 1-session 0/8 wins and 8/8 losses, 5-session 1/8 wins and 4/8 losses, 20-session 1/8 wins and 3/8 losses.
- GJR-GARCH ranked ahead of HAR at 0/3 horizons. Significant ticker comparisons at the 5% threshold were 1-session 0/8 wins and 8/8 losses, 5-session 1/8 wins and 3/8 losses, 20-session 1/8 wins and 3/8 losses.
- HAR-GARCH ranked ahead of HAR at 0/3 horizons. Significant ticker comparisons at the 5% threshold were 1-session 0/8 wins and 5/8 losses, 5-session 0/8 wins and 5/8 losses, 20-session 0/8 wins and 5/8 losses.
- HAR-X ranked ahead of HAR at 0/3 horizons. Significant ticker comparisons at the 5% threshold were 1-session 1/8 wins and 2/8 losses, 5-session 0/8 wins and 3/8 losses, 20-session 0/8 wins and 2/8 losses.

## Adaptive coverage

Each ticker and horizon chooses an individual model and a combination using pre-2022 validation MAE. The rows below compare both intervals on exactly those selected forecasts.
Adaptive updates use gamma 0.005 after the h-session outcome is observed.

| Sessions | Selected model type | Tickers | Standard coverage | Adaptive coverage | Unbounded adaptive share |
|---:|---|---:|---:|---:|---:|
| 1 | Combination | 8 | 82.5% | 89.9% | 0.2% |
| 1 | Individual | 8 | 84.6% | 89.9% | 0.3% |
| 5 | Combination | 8 | 83.7% | 89.9% | 2.7% |
| 5 | Individual | 8 | 85.2% | 90.0% | 1.6% |
| 20 | Combination | 8 | 81.7% | 89.5% | 16.4% |
| 20 | Individual | 8 | 84.1% | 90.0% | 11.6% |

Across selected ticker and horizon pairs, mean coverage changed from 83.6% to 89.9%. 19/48 pairs reached 90% adaptive coverage. Unbounded intervals cover every move and are included in both coverage and mean width.

## Data and model notes

- Forecast CSVs retain the standard HAR backtest and the original six columns.
- A three-member combination uses HAR, LHAR, and HAR-RANGE when a GJR-GARCH forecast is unavailable.
- HARQ was skipped because daily OHLCV cannot estimate intraday quarticity. A single daily return to the fourth power simply squares the daily variance proxy.
- COMI.CA — Excluded 158 zero-volume rows since 2013-01-01.
- FWRY.CA — Excluded 49 zero-volume rows since 2013-01-01.
- ETEL.CA — Excluded 195 zero-volume rows since 2013-01-01.
- HRHO.CA — Excluded 182 zero-volume rows since 2013-01-01.
- TMGH.CA — Excluded 195 zero-volume rows since 2013-01-01.
- SWDY.CA — Excluded 199 zero-volume rows since 2013-01-01.
- EAST.CA — Excluded 294 zero-volume rows since 2013-01-01.
- ABUK.CA — Excluded 336 zero-volume rows since 2013-01-01.
