"""VanderWeele & Ding (2017) E-value sensitivity analysis."""
import numpy as np


def e_value(rr: float) -> float:
    rr = max(float(rr), 1.0 / float(rr))
    return float(rr + np.sqrt(rr * (rr - 1.0)))
