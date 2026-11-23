"""Cross-fitted T-learner, econml LinearDRLearner, Qini curve & policy evaluation."""
from __future__ import annotations

import numpy as np
import pandas as pd
from econml.dr import LinearDRLearner
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import KFold


class KnownPropensity(BaseEstimator, ClassifierMixin):
    def __init__(self, p: float = 0.5):
        self.p = p

    def fit(self, X, y):
        self.classes_ = np.array([0, 1])
        return self

    def predict_proba(self, X):
        return np.column_stack([np.full(len(X), 1.0 - self.p), np.full(len(X), self.p)])


def t_learner_cate(X: np.ndarray, y: np.ndarray, t: np.ndarray, n_splits: int = 5, seed: int = 0) -> np.ndarray:
    tau = np.zeros(len(y), dtype=float)
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for tr, te in kf.split(X):
        m1 = GradientBoostingRegressor(max_depth=2, n_estimators=100, learning_rate=0.05, random_state=seed)
        m0 = GradientBoostingRegressor(max_depth=2, n_estimators=100, learning_rate=0.05, random_state=seed)
        m1.fit(X[tr][t[tr] == 1], y[tr][t[tr] == 1])
        m0.fit(X[tr][t[tr] == 0], y[tr][t[tr] == 0])
        tau[te] = m1.predict(X[te]) - m0.predict(X[te])
    return tau


def dr_learner_cate(X: np.ndarray, y: np.ndarray, t: np.ndarray, seed: int = 0):
    est = LinearDRLearner(
        model_regression=GradientBoostingRegressor(max_depth=2, n_estimators=100, random_state=seed),
        model_propensity=KnownPropensity(0.5),
        cv=5,
        random_state=seed,
    )
    est.fit(Y=y, T=t, X=X)
    tau = est.effect(X)
    lo, hi = est.effect_interval(X, alpha=0.05)
    return tau, lo, hi


def qini_curve(tau_hat: np.ndarray, y: np.ndarray, t: np.ndarray, n_points: int = 20) -> pd.DataFrame:
    order = np.argsort(-tau_hat)
    y_s, t_s = y[order], t[order]
    n_total = len(y_s)
    rows = []
    for k in np.linspace(n_total / n_points, n_total, n_points).astype(int):
        yk, tk = y_s[:k], t_s[:k]
        if tk.sum() == 0 or (1 - tk).sum() == 0:
            continue
        uplift = yk[tk == 1].mean() - yk[tk == 0].mean()
        rows.append({"frac": k / n_total, "k": int(k), "cum_uplift": float(uplift * k)})
    return pd.DataFrame(rows)
