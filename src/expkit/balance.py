"""Pre-period covariate balance via Standardised Mean Difference (SMD)."""
import numpy as np
import pandas as pd


def smd(x_t: np.ndarray, x_c: np.ndarray) -> float:
    s = np.sqrt((np.var(x_t, ddof=1) + np.var(x_c, ddof=1)) / 2.0)
    return float((np.mean(x_t) - np.mean(x_c)) / s) if s > 0 else 0.0


def balance_table(df: pd.DataFrame, covariates: list[str], arm_col: str = "arm") -> pd.DataFrame:
    t = df[arm_col] == "treatment"
    rows = []
    for col in covariates:
        xt = df.loc[t, col].to_numpy(dtype=float)
        xc = df.loc[~t, col].to_numpy(dtype=float)
        val = smd(xt, xc)
        rows.append({
            "covariate": col,
            "mean_t": float(xt.mean()),
            "mean_c": float(xc.mean()),
            "smd": val,
            "balanced": abs(val) < 0.10,
        })
    return pd.DataFrame(rows)
