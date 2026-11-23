"""One-sided non-inferiority testing for guardrail metrics."""
from scipy.stats import norm


def non_inferiority_test(
    estimate: float, se: float, margin: float, harm_direction: str = "higher", alpha: float = 0.05
) -> dict:
    z = float(norm.ppf(1.0 - alpha))
    if harm_direction == "higher":
        bound = estimate + z * se
        lower_bound = estimate - z * se
        status = "PASS" if bound < margin else ("BREACH" if lower_bound > margin else "INCONCLUSIVE")
    else:
        bound = estimate - z * se
        upper_bound = estimate + z * se
        status = "PASS" if bound > margin else ("BREACH" if upper_bound < margin else "INCONCLUSIVE")
    return {"estimate": float(estimate), "se": float(se), "one_sided_bound": float(bound), "margin": float(margin), "status": status}
