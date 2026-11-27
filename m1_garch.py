"""Fixed-parameter Student-t GARCH forecasts in daily percent-return units."""

from math import pi, sqrt

import numpy as np
import pandas as pd


GARCH_MODELS = {"GARCH": ("GARCH", 0), "GJR-GARCH": ("GARCH", 1), "EGARCH": ("EGARCH", 1)}
NORMAL_ABS_MEAN = sqrt(2 / pi)


def cumulative_forecasts(
    returns: pd.Series, parameters: pd.Series, last_variance: float, kind: str,
    horizons: tuple[int, ...],
) -> pd.DataFrame:
    """Filter observed returns from the last fit origin, then sum future variances."""
    omega, alpha, beta = (float(parameters[name]) for name in ("omega", "alpha[1]", "beta[1]"))
    gamma = float(parameters.get("gamma[1]", 0.0))
    steps = max(horizons)
    one_step = np.empty(len(returns))
    variance = last_variance

    if kind == "EGARCH":
        log_variance = np.log(variance)
        for pos, shock in enumerate(returns.to_numpy()):
            # Cap extreme standardized shocks (same +/-8 bound as the simulation below):
            # unadjusted splits/data glitches otherwise make the exponential recursion explode.
            standardized = float(np.clip(shock * np.exp(-0.5 * log_variance), -8, 8))
            log_variance = omega + beta * log_variance + alpha * (
                abs(standardized) - NORMAL_ABS_MEAN
            ) + gamma * standardized
            if not np.isfinite(log_variance) or abs(log_variance) > 300:
                raise FloatingPointError("EGARCH produced an unstable filtered log variance")
            one_step[pos] = log_variance

        # Use common simulated paths for all origins. Only the initial log variance varies.
        # Clipping future Student-t draws makes the exponential variance moment finite.
        nu = float(parameters.get("nu", np.inf))
        rng = np.random.default_rng(2021)
        n_paths = 4096
        noise = np.zeros(n_paths)
        future = np.empty((len(returns), steps))
        future[:, 0] = np.exp(one_step)
        for step in range(1, steps):
            z = (rng.standard_normal(n_paths) if not np.isfinite(nu)
                 else rng.standard_t(nu, n_paths) * sqrt((nu - 2) / nu))
            z = np.clip(z, -8, 8)
            noise = omega + beta * noise + alpha * (np.abs(z) - NORMAL_ABS_MEAN) + gamma * z
            future[:, step] = np.exp(beta**step * one_step) * np.exp(noise).mean()
    else:
        for pos, shock in enumerate(returns.to_numpy()):
            variance = omega + (alpha + gamma * (shock < 0)) * shock**2 + beta * variance
            one_step[pos] = variance
        persistence = alpha + beta + gamma / 2
        future = np.empty((len(returns), steps))
        future[:, 0] = one_step
        for step in range(1, steps):
            future[:, step] = omega + persistence * future[:, step - 1]

    if not np.isfinite(future).all() or (future <= 0).any():
        raise FloatingPointError("Nonpositive or nonfinite conditional variance")
    cumulative = np.cumsum(future, axis=1)
    return pd.DataFrame({h: cumulative[:, h - 1] for h in horizons}, index=returns.index)


def fit_volatility(
    arch_model, returns: pd.Series, estimation: pd.Series, model_name: str,
    horizons: tuple[int, ...], diagnostics: dict | None = None,
) -> pd.DataFrame:
    kind, asymmetry = GARCH_MODELS[model_name]
    result = arch_model(
        estimation, mean="Zero", vol=kind, p=1, o=asymmetry, q=1, dist="t", rescale=False,
    ).fit(disp="off", show_warning=False)
    student_nu = float(result.params.get("nu", np.nan))
    normal_fallback = student_nu < 3
    if diagnostics is not None:
        diagnostics.update(student_t_nu=student_nu, normal_fallback=normal_fallback)
    if normal_fallback:
        # Guard against fits close to the nu=2 boundary of finite Student-t variance, seen with
        # data glitches/stale prices. Refit with normal errors instead.
        result = arch_model(
            estimation, mean="Zero", vol=kind, p=1, o=asymmetry, q=1, dist="normal", rescale=False,
        ).fit(disp="off", show_warning=False)
    if result.convergence_flag:
        raise ValueError(f"optimizer returned status {result.convergence_flag}")
    last_variance = float(np.asarray(result.conditional_volatility)[-1] ** 2)
    if not np.isfinite(last_variance) or last_variance <= 0:
        raise FloatingPointError("Invalid final fitted variance")
    return cumulative_forecasts(
        returns.loc[estimation.index[-1]:], result.params, last_variance, kind, horizons,
    )


def garch_features(
    returns: pd.Series, calibration_start: pd.Timestamp, horizons: tuple[int, ...],
    diagnostics: dict[str, dict] | None = None,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, list[str]]:
    diagnostics = {} if diagnostics is None else diagnostics
    try:
        from arch import arch_model
    except ImportError:
        diagnostics.update({name: {"status": "arch_unavailable"} for name in (*GARCH_MODELS, "HAR-GARCH")})
        return {}, pd.DataFrame(), [
            "arch is unavailable. GARCH, GJR-GARCH, EGARCH, and HAR-GARCH were skipped."
        ]

    percent = 100 * returns.dropna()
    estimation = percent.loc[percent.index < calibration_start]
    forecasts = {}
    issues = []
    for name in GARCH_MODELS:
        try:
            fit = diagnostics.setdefault(name, {})
            variance = fit_volatility(arch_model, percent, estimation, name, horizons, fit)
            fit["status"] = "ok"
            forecasts[name] = np.sqrt(variance) * (NORMAL_ABS_MEAN / 100)
        except (ValueError, ArithmeticError) as error:
            diagnostics[name]["status"] = str(error)
            issues.append(f"{name} was skipped because {error}.")

    # The hybrid uses a causal training covariate with an earlier parameter cutoff.
    # Its volatility estimates start on the last session of this estimation prefix.
    try:
        prefix = estimation.iloc[: len(estimation) // 2]
        fit = diagnostics.setdefault("HAR-GARCH", {})
        variance = fit_volatility(arch_model, percent, prefix, "GARCH", horizons, fit)
        fit["status"] = "ok"
        hybrid = np.sqrt(variance) / 100
    except (ValueError, ArithmeticError) as error:
        diagnostics["HAR-GARCH"]["status"] = str(error)
        issues.append(f"HAR-GARCH was skipped because its GARCH feature failed ({error}).")
        hybrid = pd.DataFrame()
    return forecasts, hybrid, issues
