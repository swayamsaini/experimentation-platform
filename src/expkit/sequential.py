"""Always-valid mSPRT & Lan-DeMets O'Brien-Fleming group-sequential boundaries."""
import numpy as np
from scipy.stats import norm


def msprt_path(y_t: np.ndarray, y_c: np.ndarray, sigma2: float, tau2: float, alpha: float = 0.05) -> dict:
    n = np.arange(1, len(y_t) + 1)
    d = (np.cumsum(y_t) - np.cumsum(y_c)) / n
    lam = np.sqrt(2 * sigma2 / (2 * sigma2 + n * tau2)) * np.exp(
        (n ** 2 * tau2 * d ** 2) / (4 * sigma2 * (2 * sigma2 + n * tau2))
    )
    p_always = np.minimum.accumulate(np.minimum(1.0, 1.0 / lam))
    stop = int(np.argmax(lam >= 1.0 / alpha) + 1) if (lam >= 1.0 / alpha).any() else None
    return {"n": n, "lambda": lam, "p_always_valid": p_always, "stop_at": stop}


def obrien_fleming_boundaries(n_looks: int = 6, alpha: float = 0.05) -> list[dict]:
    z_a2 = norm.ppf(1.0 - alpha / 2.0)
    rows, prev_spent = [], 0.0
    for k in range(1, n_looks + 1):
        t_frac = k / n_looks
        cum_alpha = float(2.0 * (1.0 - norm.cdf(z_a2 / np.sqrt(t_frac))))
        inc_alpha = max(cum_alpha - prev_spent, 1e-12)
        z_crit = float(norm.ppf(1.0 - inc_alpha / 2.0))
        rows.append({"look": k, "info_frac": t_frac, "cum_alpha": cum_alpha, "z_boundary": z_crit})
        prev_spent = cum_alpha
    return rows
