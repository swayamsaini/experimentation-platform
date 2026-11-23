"""Sample size, Minimum Detectable Effect (MDE), and achieved power."""
import numpy as np
from scipy.stats import norm


def n_per_arm_mean(sigma: float, delta: float, alpha: float = 0.05, power: float = 0.80, ratio: float = 1.0) -> int:
    za, zb = norm.ppf(1 - alpha / 2), norm.ppf(power)
    return int(np.ceil((1 + 1 / ratio) * (za + zb) ** 2 * sigma ** 2 / delta ** 2))


def mde_mean(sigma: float, n_per_arm: int, alpha: float = 0.05, power: float = 0.80) -> float:
    za, zb = norm.ppf(1 - alpha / 2), norm.ppf(power)
    return float((za + zb) * sigma * np.sqrt(2.0 / n_per_arm))


def n_per_arm_prop(p1: float, p2: float, alpha: float = 0.05, power: float = 0.80) -> int:
    za, zb = norm.ppf(1 - alpha / 2), norm.ppf(power)
    pbar = (p1 + p2) / 2.0
    num = (za * np.sqrt(2 * pbar * (1 - pbar)) + zb * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    return int(np.ceil(num / (p1 - p2) ** 2))


def achieved_power(y: np.ndarray, t: np.ndarray, delta: float, alpha: float = 0.05) -> float:
    n1, n0 = int(t.sum()), int((~t).sum())
    se = np.sqrt(np.var(y[t], ddof=1) / n1 + np.var(y[~t], ddof=1) / n0)
    z = norm.ppf(1 - alpha / 2)
    return float(1.0 - norm.cdf(z - delta / se) + norm.cdf(-z - delta / se))
