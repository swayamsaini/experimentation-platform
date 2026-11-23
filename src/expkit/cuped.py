"""Pooled CUPED, exact Welch-Satterthwaite test, winsorisation, and Lin's estimator."""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats


def winsorise(y: np.ndarray, p: float = 0.99, lower: bool = False) -> np.ndarray:
    y = np.asarray(y, dtype=float).copy()
    hi = np.quantile(y, p)
    y = np.minimum(y, hi)
    if lower:
        y = np.maximum(y, np.quantile(y, 1.0 - p))
    return y


def welch_test(y: np.ndarray, t: np.ndarray, alpha: float = 0.05) -> dict:
    a, b = np.asarray(y[t], dtype=float), np.asarray(y[~t], dtype=float)
    na, nb = len(a), len(b)
    va, vb = np.var(a, ddof=1), np.var(b, ddof=1)
    est = float(a.mean() - b.mean())
    se = float(np.sqrt(va / na + vb / nb))
    denom = (va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)
    df = ((va / na + vb / nb) ** 2) / denom if denom > 0 else float(na + nb - 2)
    t_crit = float(stats.t.ppf(1.0 - alpha / 2.0, df))
    res = stats.ttest_ind(a, b, equal_var=False)
    return {
        "estimate": est,
        "se": se,
        "ci_lo": est - t_crit * se,
        "ci_hi": est + t_crit * se,
        "p_value": float(res.pvalue),
        "df": float(df),
    }


def cuped_adjust(y: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, float]:
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    vx = np.var(x, ddof=1)
    theta = float(np.cov(x, y, ddof=1)[0, 1] / vx) if vx > 0 else 0.0
    return y - theta * (x - x.mean()), theta


def variance_reduction(y: np.ndarray, y_adj: np.ndarray) -> float:
    vy = np.var(y, ddof=1)
    return float(1.0 - np.var(y_adj, ddof=1) / vy) if vy > 0 else 0.0


def lin_estimator(df: pd.DataFrame, outcome: str, covariates: list[str], arm_col: str = "arm") -> dict:
    work = df[[outcome, arm_col] + covariates].copy()
    work["treat"] = (work[arm_col] == "treatment").astype(float)
    terms = []
    for c in covariates:
        c_name = f"{c}_c"
        work[c_name] = work[c].astype(float) - work[c].astype(float).mean()
        terms.append(c_name)
        terms.append(f"treat:{c_name}")
    formula = f"{outcome} ~ treat + " + " + ".join(terms)
    m = smf.ols(formula, data=work).fit(cov_type="HC3")
    ci = m.conf_int().loc["treat"]
    return {
        "estimate": float(m.params["treat"]),
        "se": float(m.bse["treat"]),
        "ci_lo": float(ci[0]),
        "ci_hi": float(ci[1]),
        "p_value": float(m.pvalues["treat"]),
    }
