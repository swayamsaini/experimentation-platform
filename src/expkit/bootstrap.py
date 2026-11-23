"""Unit-level percentile bootstrap confidence interval."""
import numpy as np


def bootstrap_diff(y: np.ndarray, t: np.ndarray, stat=np.mean, n_boot: int = 5000, seed: int = 7, alpha: float = 0.05) -> dict:
    rng = np.random.default_rng(seed)
    a, b = np.asarray(y[t], dtype=float), np.asarray(y[~t], dtype=float)
    idx_a = rng.integers(0, len(a), size=(n_boot, len(a)))
    idx_b = rng.integers(0, len(b), size=(n_boot, len(b)))
    diffs = stat(a[idx_a], axis=1) - stat(b[idx_b], axis=1)
    lo, hi = np.quantile(diffs, [alpha / 2.0, 1.0 - alpha / 2.0])
    return {"estimate": float(stat(a) - stat(b)), "ci_lo": float(lo), "ci_hi": float(hi)}
