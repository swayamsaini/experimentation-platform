"""Delta method inference for ratio metrics (AOV, late_rate, cancel_rate)."""
import numpy as np
from scipy.stats import norm


def ratio_estimate(num: np.ndarray, den: np.ndarray) -> tuple[float, float]:
    num, den = np.asarray(num, dtype=float), np.asarray(den, dtype=float)
    n = len(num)
    mn, md = num.mean(), den.mean()
    r = mn / md
    var = (
        np.var(num, ddof=1)
        - 2 * r * np.cov(num, den, ddof=1)[0, 1]
        + r ** 2 * np.var(den, ddof=1)
    ) / (n * md ** 2)
    return float(r), float(np.sqrt(max(var, 0.0)))


def ratio_diff(num_t, den_t, num_c, den_c, alpha: float = 0.05) -> dict:
    rt, st = ratio_estimate(num_t, den_t)
    rc, sc = ratio_estimate(num_c, den_c)
    se = float(np.sqrt(st ** 2 + sc ** 2))
    d = rt - rc
    z = float(norm.ppf(1.0 - alpha / 2.0))
    p = float(2.0 * (1.0 - norm.cdf(abs(d) / se))) if se > 0 else 1.0
    return {"estimate": d, "se": se, "ci_lo": d - z * se, "ci_hi": d + z * se, "p_value": p, "r_t": rt, "r_c": rc}
