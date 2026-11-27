"""Optional zero-shot CPU forecasts of the daily log absolute-return proxy."""

from functools import lru_cache

import numpy as np
import pandas as pd


MODEL_PATH = "ibm-granite/granite-timeseries-ttm-r2"
CONTEXT_LENGTH = 512
CHECKPOINT_PREDICTION_LENGTH = 96
BATCH_SIZE = 128
RETURN_FLOOR = 1e-5
TTM_MODELS = ("TTM", "TTM+Log-HAR")


@lru_cache(maxsize=1)
def load_model():
    try:
        from tsfm_public.toolkit.get_model import get_model
        import torch
    except ImportError as error:
        return None, None, f"TTM and TTM+Log-HAR were skipped because tsfm_public or its dependencies are unavailable ({error})."

    try:
        torch.set_num_threads(min(4, torch.get_num_threads()))
        model = get_model(
            MODEL_PATH, context_length=CONTEXT_LENGTH,
            prediction_length=CHECKPOINT_PREDICTION_LENGTH,
        ).to("cpu").eval()
        return model, torch, None
    except (OSError, RuntimeError, ValueError, ImportError) as error:
        return None, None, f"TTM and TTM+Log-HAR were skipped because the checkpoint could not load ({error})."


def ttm_forecasts(
    returns: pd.Series, origins: pd.DatetimeIndex, horizons: tuple[int, ...],
) -> tuple[pd.DataFrame, str | None]:
    """Use a 512-session trailing window ending at each requested forecast origin."""
    series = returns.dropna()
    positions = np.flatnonzero(series.index.isin(origins))
    positions = positions[positions >= CONTEXT_LENGTH - 1]
    if len(positions) == 0:
        return pd.DataFrame(), "TTM was skipped because no forecast origin has 512 usable returns."

    model, torch, issue = load_model()
    if model is None:
        return pd.DataFrame(), issue

    proxy = np.log(series.abs().clip(lower=RETURN_FLOOR).to_numpy())
    windows = np.lib.stride_tricks.sliding_window_view(proxy, CONTEXT_LENGTH)
    batches = []
    steps = max(horizons)
    try:
        with torch.inference_mode(), np.errstate(over="raise", invalid="raise"):
            for first in range(0, len(positions), BATCH_SIZE):
                end = positions[first:first + BATCH_SIZE]
                context = windows[end - CONTEXT_LENGTH + 1]
                center = context.mean(axis=1, keepdims=True)
                scale = context.std(axis=1, keepdims=True)
                scale[scale == 0] = 1
                normalized = (context - center) / scale
                past = torch.as_tensor(normalized[:, :, None], dtype=torch.float32, device="cpu")
                prediction = model(past_values=past).prediction_outputs
                log_abs = prediction[:, :steps, 0].cpu().numpy() * scale + center
                if log_abs.shape != (len(end), steps) or not np.isfinite(log_abs).all():
                    raise ValueError("The checkpoint returned invalid prediction steps.")
                # The normal scale factors cancel when aggregating daily variances
                # and converting back to expected absolute cumulative return.
                daily_abs = np.exp(np.maximum(log_abs, np.log(RETURN_FLOOR)))
                cumulative = np.sqrt(np.cumsum(np.square(daily_abs), axis=1))
                batches.append(cumulative[:, np.asarray(horizons) - 1])
    except (RuntimeError, ValueError, FloatingPointError) as error:
        return pd.DataFrame(), f"TTM and TTM+Log-HAR were skipped because inference failed ({error})."

    return pd.DataFrame(np.concatenate(batches), columns=horizons, index=series.index[positions]), None
