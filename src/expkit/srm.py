"""Sample Ratio Mismatch chi-square gate."""
import numpy as np
from scipy.stats import chisquare


def srm_test(counts: dict[str, int], expected_ratio: dict[str, float], alpha: float = 1e-3) -> dict:
    arms = list(counts)
    obs = np.array([counts[a] for a in arms], dtype=float)
    exp = np.array([expected_ratio[a] for a in arms], dtype=float)
    exp = exp / exp.sum() * obs.sum()
    stat, p = chisquare(obs, exp)
    return {
        "chi2": float(stat),
        "p_value": float(p),
        "srm_detected": bool(p < alpha),
        "observed": dict(zip(arms, obs.astype(int))),
    }
