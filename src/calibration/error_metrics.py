"""Error metrics that compare simulated trajectories to historical data.

All metrics are robust to NaNs in the observed series — historical CSVs
have gaps, and the optimizer must not poison itself by computing on them.
"""
from __future__ import annotations

from typing import Dict, Iterable, Optional, Tuple

import numpy as np


def mae(predicted: np.ndarray, observed: np.ndarray) -> float:
    """Mean absolute error, ignoring NaNs in observed."""
    pred, obs = _align(predicted, observed)
    if len(obs) == 0:
        return 0.0
    return float(np.mean(np.abs(pred - obs)))


def rmse(predicted: np.ndarray, observed: np.ndarray) -> float:
    """Root mean squared error, ignoring NaNs in observed."""
    pred, obs = _align(predicted, observed)
    if len(obs) == 0:
        return 0.0
    return float(np.sqrt(np.mean((pred - obs) ** 2)))


def mae_normalized(
    predicted: np.ndarray, observed: np.ndarray, range_max: float
) -> float:
    """MAE divided by the metric's range, so errors across metrics are comparable."""
    if range_max <= 0:
        return float("nan")
    return mae(predicted, observed) / range_max


def rmse_normalized(
    predicted: np.ndarray, observed: np.ndarray, range_max: float
) -> float:
    if range_max <= 0:
        return float("nan")
    return rmse(predicted, observed) / range_max


def weighted_error(
    predicted_by_series: Dict[str, np.ndarray],
    observed_by_series: Dict[str, np.ndarray],
    ranges: Dict[str, float],
    weights: Optional[Dict[str, float]] = None,
) -> Tuple[float, Dict[str, float]]:
    """Weighted aggregate of normalized MAEs across series.

    Returns the scalar aggregate plus a per-series breakdown for inspection.
    Series missing from ``observed_by_series`` or with all-NaN values
    contribute zero (and zero weight).
    """
    weights = weights or {}
    total_weight = 0.0
    total = 0.0
    breakdown: Dict[str, float] = {}
    for sid, pred in predicted_by_series.items():
        obs = observed_by_series.get(sid)
        if obs is None:
            continue
        rng = ranges.get(sid, 1.0)
        e = mae_normalized(pred, obs, rng)
        if np.isnan(e):
            continue
        breakdown[sid] = e
        w = float(weights.get(sid, 1.0))
        total += e * w
        total_weight += w
    aggregate = total / total_weight if total_weight > 0 else 0.0
    return aggregate, breakdown


# ---------------------------------------------------------------------------- helpers


def _align(predicted: np.ndarray, observed: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Return predicted and observed arrays restricted to indices where observed is finite."""
    pred = np.asarray(predicted, dtype=float)
    obs = np.asarray(observed, dtype=float)
    n = min(len(pred), len(obs))
    pred, obs = pred[:n], obs[:n]
    mask = ~np.isnan(obs) & ~np.isnan(pred)
    return pred[mask], obs[mask]
