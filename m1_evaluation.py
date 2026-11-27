"""Forecast combinations, conformal ranges, and paired test statistics."""

from collections import deque
from math import ceil, erfc, sqrt

import numpy as np
import pandas as pd


ALPHA = 0.10
GAMMA = 0.005
SUMMARY_COLUMNS = [
    "horizon", "model", "avg_mae_rank", "n_tickers", "mean_MAE",
    "significant_wins_vs_har", "significant_losses_vs_har",
]


def combination_points(
    points: pd.DataFrame, targets: pd.Series, members: list[str],
) -> pd.DataFrame:
    x = points[members]
    suffix = "" if len(members) == 4 else " (3 members)"
    forecasts = pd.DataFrame({f"Combo Equal{suffix}": x.mean(axis=1, skipna=False)})
    training = x.loc[targets.index].join(targets.rename("actual")).dropna()
    if len(training) < 8:
        return forecasts

    member_points = training[members].to_numpy()
    y = training["actual"].to_numpy()
    mse = ((member_points - y[:, None]) ** 2).mean(axis=0)
    precision = 1 / np.maximum(mse, 1e-16)
    forecasts[f"Combo Inv-MSE{suffix}"] = x @ (precision / precision.sum())

    center = member_points.mean(axis=0)
    scale = member_points.std(axis=0)
    scale[scale == 0] = 1
    z = (member_points - center) / scale
    # Ridge penalty 10 on standardized coefficients; the intercept is unpenalized.
    gram = z.T @ z + 10 * np.eye(len(members))
    weights = np.linalg.solve(gram, z.T @ (y - y.mean()))
    forecasts[f"Combo Ridge{suffix}"] = (y.mean() + ((x - center) / scale) @ weights).clip(lower=0)
    return forecasts


def best_on_validation(points: pd.DataFrame, actual: pd.Series) -> str | None:
    if points.empty:
        return None
    errors = points.reindex(actual.index).sub(actual, axis=0).abs()
    paired = errors.dropna()
    return str(paired.mean().idxmin()) if not paired.empty else None


def conformal_quantile(sorted_scores: np.ndarray, alpha: float) -> float:
    """Finite-sample split conformal order statistic, including limiting sets."""
    rank = ceil((1 - alpha) * (len(sorted_scores) + 1) - 1e-12)
    if rank > len(sorted_scores):
        return np.inf
    if rank < 1:
        return -np.inf
    return float(sorted_scores[rank - 1])


def conformal_radius(scores: np.ndarray) -> float:
    if len(scores) < 9:
        raise ValueError("A finite 90% conformal range needs at least 9 calibration rows.")
    return conformal_quantile(np.sort(scores), ALPHA)


def adaptive_ranges(forecasts: pd.DataFrame, scores: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Use the issued interval's error once its target close has arrived."""
    pending = deque()
    sorted_scores = np.sort(scores)
    lower = np.empty(len(forecasts))
    upper = np.empty(len(forecasts))
    revealed = misses = 0

    points = forecasts["point"].to_numpy()
    actual = forecasts["actual"].to_numpy()
    target_dates = forecasts["target_date"].array

    for i, origin in enumerate(forecasts.index):
        while pending and pending[0][0] <= origin:
            _, issued = pending.popleft()
            revealed += 1
            misses += not lower[issued] <= actual[issued] <= upper[issued]
        alpha = ALPHA + GAMMA * (ALPHA * revealed - misses)
        radius = conformal_quantile(sorted_scores, alpha)
        lower[i] = max(points[i] - radius, 0)
        upper[i] = points[i] + radius
        if pd.notna(target_dates[i]):
            pending.append((target_dates[i], i))
    return lower, upper


def dm_test(loss_difference: np.ndarray, horizon: int) -> tuple[float, float]:
    """Two-sided normal DM test with Bartlett/Newey–West lags h-1."""
    n = len(loss_difference)
    if n < max(horizon, 2):
        return np.nan, np.nan
    center = loss_difference.mean()
    residuals = loss_difference - center
    long_run_variance = float(residuals @ residuals / n)
    for lag in range(1, horizon):
        covariance = residuals[lag:] @ residuals[:-lag] / n
        long_run_variance += 2 * (1 - lag / horizon) * covariance
    if long_run_variance <= 0:
        return np.nan, np.nan
    statistic = center / sqrt(long_run_variance / n)
    return statistic, erfc(abs(statistic) / sqrt(2))


def summarize_results(metrics: pd.DataFrame) -> pd.DataFrame:
    ranks = metrics.groupby(["ticker", "horizon"])["MAE"].rank(method="average")
    significant = metrics["dm_pvalue_vs_har"].lt(0.05)
    return (
        metrics.assign(
            rank=ranks,
            win=significant & metrics["dm_stat"].lt(0),
            loss=significant & metrics["dm_stat"].gt(0),
        )
        .groupby(["horizon", "model"], as_index=False)
        .agg(
            avg_mae_rank=("rank", "mean"), n_tickers=("ticker", "nunique"),
            mean_MAE=("MAE", "mean"), significant_wins_vs_har=("win", "sum"),
            significant_losses_vs_har=("loss", "sum"),
        )
        .sort_values(["horizon", "avg_mae_rank", "mean_MAE", "model"], ignore_index=True)
        .reindex(columns=SUMMARY_COLUMNS)
    )
