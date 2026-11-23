"""A/A false-positive, CI coverage, and peeking-vs-mSPRT simulation checks."""
import numpy as np
from scipy import stats
from expkit.cuped import welch_test
from expkit.sequential import msprt_path


def simulate_experiment(y: np.ndarray, n_sims: int = 3000, effect: float = 0.0, seed: int = 1) -> dict:
    rng = np.random.default_rng(seed)
    n = len(y)
    rejections = 0
    covered = 0
    ests = []
    true_ate = effect * float(y.mean())
    base_arms = np.r_[np.ones(n // 2, dtype=bool), np.zeros(n - n // 2, dtype=bool)]
    for _ in range(n_sims):
        arm = rng.permutation(base_arms)
        y_obs = y + arm * effect * y
        res = welch_test(y_obs, arm)
        rejections += res["p_value"] < 0.05
        covered += res["ci_lo"] <= true_ate <= res["ci_hi"]
        ests.append(res["estimate"])
    return {"reject_rate": rejections / n_sims, "coverage": covered / n_sims, "bias": float(np.mean(ests) - true_ate)}


def simulate_peeking_vs_msprt(n_sims: int = 1500, n_days: int = 14, per_day: int = 40, seed: int = 3) -> dict:
    rng = np.random.default_rng(seed)
    fp_peek, fp_msprt, fp_fixed = 0, 0, 0
    for _ in range(n_sims):
        a = rng.normal(size=(n_days, per_day))
        b = rng.normal(size=(n_days, per_day))
        for d in range(2, n_days + 1):
            if stats.ttest_ind(a[:d].ravel(), b[:d].ravel(), equal_var=False).pvalue < 0.05:
                fp_peek += 1
                break
        if stats.ttest_ind(a.ravel(), b.ravel(), equal_var=False).pvalue < 0.05:
            fp_fixed += 1
        if msprt_path(a.ravel(), b.ravel(), sigma2=1.0, tau2=0.04, alpha=0.05)["stop_at"] is not None:
            fp_msprt += 1
    return {"peeking_fpr": fp_peek / n_sims, "msprt_fpr": fp_msprt / n_sims, "fixed_fpr": fp_fixed / n_sims}


if __name__ == "__main__":
    print("Peeking vs mSPRT:", simulate_peeking_vs_msprt())
