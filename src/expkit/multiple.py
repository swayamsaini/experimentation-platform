"""Holm (FWER) and Benjamini-Hochberg (FDR) multiple-testing corrections."""
import numpy as np


def holm(pvals: list[float], alpha: float = 0.05) -> np.ndarray:
    p = np.asarray(pvals, dtype=float)
    m = len(p)
    order = np.argsort(p)
    reject = np.zeros(m, dtype=bool)
    for rank, idx in enumerate(order):
        if p[idx] <= alpha / (m - rank):
            reject[idx] = True
        else:
            break
    return reject


def benjamini_hochberg(pvals: list[float], q: float = 0.05) -> np.ndarray:
    p = np.asarray(pvals, dtype=float)
    m = len(p)
    order = np.argsort(p)
    thresh = q * (np.arange(1, m + 1) / m)
    below = p[order] <= thresh
    k = int(np.max(np.where(below)[0]) + 1) if below.any() else 0
    reject = np.zeros(m, dtype=bool)
    reject[order[:k]] = True
    return reject
