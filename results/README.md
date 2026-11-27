# M1 results

M1 predicts absolute adjusted-close log returns for 1, 5, and 20 retained trading sessions.
Forecast CSVs show the HAR backtest by forecast origin. m1_results.csv includes all three models.
Errors and widths are in decimal log-return units. Coverage is the fraction of test outcomes inside the range.

## Mean across ticker and horizon pairs

| Model | MAE | RMSE | Coverage | Average width |
|---|---:|---:|---:|---:|
| HAR | 3.41% | 4.77% | 85.0% | 9.75% |
| Log-HAR | 3.39% | 4.77% | 85.1% | 9.66% |
| Naive | 3.37% | 4.80% | 84.7% | 9.93% |

## Data and evaluation notes

- COMI.CA — Excluded 158 zero-volume rows since 2013-01-01.
- FWRY.CA — Excluded 49 zero-volume rows since 2013-01-01.
- ETEL.CA — Excluded 195 zero-volume rows since 2013-01-01.
- HRHO.CA — Excluded 182 zero-volume rows since 2013-01-01.
- TMGH.CA — Excluded 195 zero-volume rows since 2013-01-01.
- SWDY.CA — Excluded 199 zero-volume rows since 2013-01-01.
- EAST.CA — Excluded 294 zero-volume rows since 2013-01-01.
- ABUK.CA — Excluded 336 zero-volume rows since 2013-01-01.
- EFIH.CA — Excluded 43 zero-volume rows since 2013-01-01.
- EFIH.CA — Horizon 1 has insufficient pre-2022 history (15 fit rows, 5 calibration rows).
- EFIH.CA — Horizon 5 has insufficient pre-2022 history (8 fit rows, 4 calibration rows).
- EFIH.CA — Horizon 20 has insufficient pre-2022 history (0 fit rows, 1 calibration rows).
- ORAS.CA — Excluded 1241 zero-volume rows since 2013-01-01.
- ORAS.CA — Horizon 1 has insufficient pre-2022 history (16 fit rows, 5 calibration rows).
- ORAS.CA — Horizon 5 has insufficient pre-2022 history (9 fit rows, 4 calibration rows).
- ORAS.CA — Horizon 20 has insufficient pre-2022 history (0 fit rows, 1 calibration rows).
