"""Trimmed IPW, Doubly Robust AIPW, and seller-clustered bootstrap."""
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression


def ipw_ate(X: np.ndarray, t: np.ndarray, y: np.ndarray, clip: tuple[float, float] = (0.02, 0.98)) -> dict:
    ps = LogisticRegression(max_iter=1000).fit(X, t).predict_proba(X)[:, 1]
    keep = (ps >= clip[0]) & (ps <= clip[1])
    ps_k, t_k, y_k = ps[keep], t[keep], y[keep]
    ate = float(
        np.average(y_k[t_k == 1], weights=1.0 / ps_k[t_k == 1])
        - np.average(y_k[t_k == 0], weights=1.0 / (1.0 - ps_k[t_k == 0]))
    )
    return {"ate": ate, "ps": ps, "kept_frac": float(keep.mean())}


def aipw_ate(X: np.ndarray, t: np.ndarray, y: np.ndarray, clip: tuple[float, float] = (0.02, 0.98), seed: int = 0) -> dict:
    ps = np.clip(LogisticRegression(max_iter=1000).fit(X, t).predict_proba(X)[:, 1], *clip)
    m1 = GradientBoostingRegressor(max_depth=3, n_estimators=80, random_state=seed).fit(X[t == 1], y[t == 1])
    m0 = GradientBoostingRegressor(max_depth=3, n_estimators=80, random_state=seed).fit(X[t == 0], y[t == 0])
    mu1, mu0 = m1.predict(X), m0.predict(X)
    psi = (mu1 - mu0) + t * (y - mu1) / ps - (1.0 - t) * (y - mu0) / (1.0 - ps)
    return {"ate": float(psi.mean()), "se_iid": float(psi.std(ddof=1) / np.sqrt(len(psi))), "ps": ps}
