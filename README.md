# EGX Risk Radar

M1 forecasts the size of daily Egyptian stock moves over 1, 5, and 20 trading sessions. It compares HAR, GARCH, and combined forecasts with standard and adaptive conformal ranges. The Streamlit demo displays the most recent usable price date, the latest forecast, and observed coverage on historical test data.

## Run locally

Run these commands from the repository root in PowerShell with Python 3.14.

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python m1_har.py
streamlit run app.py
```

To refresh the Yahoo Finance cache, run `python collect_egx.py` before running M1. The model and demo can use the existing `prices/` CSVs offline. Select a watchlist ticker in the sidebar, or type a Yahoo ticker such as `COMI.CA` to request a live download. When a live request fails, the demo uses the matching local cache if available.

## Models

- **HAR**, **Log-HAR**, and **Naive** are the original baselines. HAR uses trailing means of absolute daily log returns over 1, 5, and 22 sessions. Log-HAR logs the three means with a floor of 1e-8. Naive scales the 22-session mean by the square root of the horizon.
- **HAR-RV** uses trailing means of squared daily log returns. **HAR-RANGE** uses trailing Parkinson and Garman–Klass variance estimates from daily OHLC. Negative Garman–Klass estimates are floored at zero.
- **LHAR** adds the current negative-return flag to HAR. **HAR-X** also uses the prior session's log volume relative to the preceding 22-session mean log volume, the absolute open-to-prior-close log gap, and the equal-weight mean absolute adjusted-close log return among available EGX watchlist tickers that day. For dates without an EGX observation, the market feature uses the latest available date.
- **GARCH(1,1)**, **GJR-GARCH(1,1,1)**, and **EGARCH(1,1,1)** use `arch` to estimate zero-mean Student-t models on percent returns before the earliest calibration origin. Subsequent observations update conditional variance with fixed parameters. The point forecast uses `sqrt(sum of forecast daily variances) * sqrt(2/pi) / 100`, a zero-mean normal approximation to expected absolute cumulative log return. EGARCH uses 4,096 seeded paths with future standardized Student-t innovations clipped to ±8 for a finite multi-step variance approximation. [arch forecasting](https://arch.readthedocs.io/en/stable/univariate/forecasting.html)
- **HAR-GARCH** adds the GARCH cumulative conditional standard deviation to HAR-X. Its GARCH parameters use an earlier fitting prefix so that every historical hybrid regressor uses parameters available at its own forecast date.
- **Combo Equal**, **Combo Inv-MSE**, and **Combo Ridge** use HAR, LHAR, HAR-RANGE, and GJR-GARCH. The ridge stack is optional and uses a fixed penalty of 10 on standardized predictors. If GJR-GARCH is unavailable, separately labeled three-member variants use the three HAR forecasts. **HARQ** requires intraday returns for a meaningful quarticity estimate. [HARQ paper](https://public.econ.duke.edu/%7Eget/browse/courses/pbc/Readings/BollerslevPattonQuaedvliegJoE2016.pdf)

## Evaluation and outputs

- M1 uses daily data from January 1, 2013 onward and removes zero-volume and invalid adjusted-price rows before calculating returns. Each target is `abs(log(P[t+h] / P[t]))` for 1, 5, or 20 retained sessions.
- Each horizon reserves the last 20% of eligible pre-2022 labeled rows for calibration, rounding up. Fit outcomes finish before the first calibration origin. Calibration outcomes finish before January 1, 2022, and test forecasts originate from that date onward.
- Learned blend weights use the first half of calibration, with a target-date purge before the second half. The remaining residuals set those blends' conformal radii. Predefined models use the full calibration window. An early chronological validation split picks the individual model and combination for adaptive evaluation by ticker and horizon. Candidate blend weights are fitted before that validation split. The app defaults to the pre-test selection for its chosen horizon.
- Split conformal ranges use the finite-sample order statistic of absolute calibration residuals, with a zero lower bound for nonempty ranges. Adaptive conformal inference updates alpha with step size 0.005 using the original issued interval when its outcome becomes available after h sessions. It can yield unbounded or empty ranges. Test coverage counts those outcomes and the dashboard discloses unbounded frequency. [Gibbs and Candès (2021)](https://papers.neurips.cc/paper_files/paper/2021/file/0d441de75945e5acbc865406fc9a2559-Paper.pdf)
- The [Diebold–Mariano test](https://doi.org/10.1080/07350015.1995.10524599) compares paired absolute errors to HAR using a two-sided normal p-value and Newey–West variance with h−1 lags. Negative statistics favor the candidate. Significance counts use unadjusted p-values below 0.05.
- `results/m1_results.csv` contains per-ticker model metrics, DM statistics and p-values, and adaptive coverage where evaluated. `results/m1_summary.csv` holds the per-horizon average MAE ranks and significant win counts. `results/forecasts_<ticker>.csv` retains the original six-column standard HAR backtest by forecast origin. CSV returns and widths are decimals, and the app displays absolute log returns as percentages. `results/README.md` summarizes the run and unavailable models.

## Push to GitHub and enable Actions

Create an empty GitHub repository. From the project folder, initialize Git if needed, then stage the project and add its GitHub remote. Replace `YOUR-ACCOUNT` and `YOUR-REPOSITORY` with your GitHub values.

```
git init -b main
git add .gitignore .github README.md requirements.txt collect_egx.py tickers.txt m1_har.py m1_garch.py m1_evaluation.py app.py prices results
git commit -m "Add EGX Risk Radar M1"
git remote add origin https://github.com/YOUR-ACCOUNT/YOUR-REPOSITORY.git
git push -u origin main
```

If the repository already has an `origin`, use that remote or update it with `git remote set-url origin <url>`. On GitHub, open **Settings → Actions → General** and allow GitHub Actions and the checkout and setup-python actions. The workflow requests `contents: write` so it can commit changed prices and results. Repository and branch rules must permit the workflow bot to push.

Open **Actions → Collect EGX prices and refresh M1 → Run workflow** for a manual run. The scheduled workflow runs on the default branch at 15:00 UTC Sunday through Thursday. [GitHub Actions manual runs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow) · [GitHub Actions schedule](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)

## Deploy free on Streamlit Community Cloud

Sign in to Streamlit Community Cloud, connect your GitHub account, and choose **Create app**. Select your repository and branch, set **Main file path** to `app.py`, and click **Deploy**. Community Cloud installs the root `requirements.txt`. Keep the `prices/` CSVs in the repository to make them available on the deployed app. [Streamlit Community Cloud deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app)
