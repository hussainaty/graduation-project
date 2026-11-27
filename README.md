# EGX Risk Radar

M1 forecasts the size of daily Egyptian stock moves over 1, 5, and 20 trading sessions. It uses adjusted prices, HAR regressions, and split-conformal ranges. The Streamlit demo displays the most recent usable price date, the latest forecast, and observed coverage on historical test data.

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

## Model and outputs

- M1 uses daily data from January 1, 2013 onward. It removes zero-volume and invalid rows before calculating returns, so horizons count retained sessions. The price target is `abs(log(P[t+h] / P[t]))` using adjusted closes.
- HAR uses trailing means of absolute daily log returns over 1, 5, and 22 sessions. Log-HAR applies a log to those three features, using a floor of 1e-8, and fits the same target. Both use ordinary least squares with an intercept and clip point estimates at zero. The naive point forecast is the 22-session mean times the square root of the horizon.
- Each horizon reserves the last 20% of eligible pre-2022 labeled rows for calibration, rounding up to a whole row. Targets must finish before the calibration boundary for fitting and before January 1, 2022 for calibration. Test forecasts start on January 1, 2022 or later. The latest forecast uses features as of the latest usable test-period price, without waiting for its outcome.
- Each model uses the finite-sample 90% order statistic of absolute calibration residuals as its range radius. Lower bounds are clipped at zero. A ticker needs at least nine calibration rows for a finite range and at least four fit rows for the regression. Time dependence and changes in volatility can affect realized coverage.
- `results/m1_results.csv` contains the full model comparison by ticker and horizon. `results/forecasts_<ticker>.csv` contains the HAR backtest by forecast origin, with dots replaced by underscores in the filename. `results/README.md` describes the scores and data gaps. The CSV stores returns and widths as decimals. The app multiplies log returns by 100 for display.

## Push to GitHub and enable Actions

Create an empty GitHub repository. From the project folder, initialize Git if needed, then stage the project and add its GitHub remote. Replace `YOUR-ACCOUNT` and `YOUR-REPOSITORY` with your GitHub values.

```
git init -b main
git add .gitignore .github README.md requirements.txt collect_egx.py tickers.txt m1_har.py app.py prices results
git commit -m "Add EGX Risk Radar M1"
git remote add origin https://github.com/YOUR-ACCOUNT/YOUR-REPOSITORY.git
git push -u origin main
```

If the repository already has an `origin`, use that remote or update it with `git remote set-url origin <url>`. On GitHub, open **Settings → Actions → General** and allow GitHub Actions and the checkout and setup-python actions. The workflow requests `contents: write` so it can commit changed prices and results. Repository and branch rules must permit the workflow bot to push.

Open **Actions → Collect EGX prices and refresh M1 → Run workflow** for a manual run. The scheduled workflow runs on the default branch at 15:00 UTC Sunday through Thursday. [GitHub Actions manual runs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow) · [GitHub Actions schedule](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)

## Deploy free on Streamlit Community Cloud

Sign in to Streamlit Community Cloud, connect your GitHub account, and choose **Create app**. Select your repository and branch, set **Main file path** to `app.py`, and click **Deploy**. Community Cloud installs the root `requirements.txt`. Keep the `prices/` CSVs in the repository to make them available on the deployed app. [Streamlit Community Cloud deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app)
