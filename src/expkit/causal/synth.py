"""Synthetic Control with SLSQP donor weights & placebo-in-space RMSPE p-value."""
import numpy as np
from scipy.optimize import minimize


def synth_weights(y_treated_pre: np.ndarray, Y_donors_pre: np.ndarray) -> np.ndarray:
    j_dim = Y_donors_pre.shape[1]
    loss = lambda w: float(np.sum((y_treated_pre - Y_donors_pre @ w) ** 2))
    cons = ({"type": "eq", "fun": lambda w: np.sum(w) - 1.0},)
    res = minimize(loss, np.full(j_dim, 1.0 / j_dim), bounds=[(0.0, 1.0)] * j_dim, constraints=cons, method="SLSQP")
    return res.x


def synth_effect(y_treated: np.ndarray, Y_donors: np.ndarray, T0: int) -> dict:
    w = synth_weights(y_treated[:T0], Y_donors[:T0])
    synth = Y_donors @ w
    gap = y_treated - synth
    pre_rmspe = float(np.sqrt(np.mean(gap[:T0] ** 2)))
    post_rmspe = float(np.sqrt(np.mean(gap[T0:] ** 2)))
    ratio = post_rmspe / pre_rmspe if pre_rmspe > 1e-12 else float("inf")
    return {
        "gap": gap,
        "weights": w,
        "synth": synth,
        "pre_rmspe": pre_rmspe,
        "post_rmspe": post_rmspe,
        "rmspe_ratio": ratio,
        "post_mean_gap": float(gap[T0:].mean()),
    }


def placebo_in_space_pvalue(Y_panel: np.ndarray, treated_idx: int, T0: int) -> dict:
    n_units = Y_panel.shape[1]
    ratios = []
    for j in range(n_units):
        res = synth_effect(Y_panel[:, j], np.delete(Y_panel, j, axis=1), T0)
        ratios.append((j, res["rmspe_ratio"], res["post_mean_gap"]))
    treated_ratio = [r[1] for r in ratios if r[0] == treated_idx][0]
    return {"treated_rmspe_ratio": treated_ratio, "p_value": float(np.mean([r[1] >= treated_ratio for r in ratios]))}
