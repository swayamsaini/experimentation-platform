"""Run complete experiment + causal analyses, Monte Carlo impact, and export to results.duckdb."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd

from expkit.metrics import verify_three_route_gmv
from expkit.srm import srm_test
from expkit.balance import balance_table
from expkit.power import mde_mean, achieved_power
from expkit.cuped import winsorise, welch_test, cuped_adjust, variance_reduction, lin_estimator
from expkit.ratio import ratio_diff
from expkit.guardrails import non_inferiority_test
from expkit.multiple import benjamini_hochberg
from expkit.sequential import obrien_fleming_boundaries
from expkit.causal.did import load_strike_orders, fit_event_study, run_did_robustness

WAREHOUSE = "data/warehouse/olist.duckdb"
EXPORT_DB = Path("data/exports/results.duckdb")
MEMO_JSON = Path("data/exports/memo_figures.json")


def git_commit_hash() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "uncommitted"


def monte_carlo_impact(
    est_rel: float, se_rel: float, baseline_gmv_6w: float, n_sellers: int,
    take_rate_range=(0.08, 0.14), cost_wk_range=(20.0, 60.0), n_draws: int = 20000, seed: int = 11
) -> dict:
    rng = np.random.default_rng(seed)
    lift = rng.normal(est_rel, se_rel, n_draws)
    take = rng.uniform(*take_rate_range, n_draws)
    cost = rng.uniform(*cost_wk_range, n_draws)
    wk_base = baseline_gmv_6w / 6.0
    net_wk = n_sellers * (lift * wk_base * take - cost)
    return {
        "median_net_wk_brl": float(np.median(net_wk)),
        "p10_net_wk_brl": float(np.quantile(net_wk, 0.10)),
        "p90_net_wk_brl": float(np.quantile(net_wk, 0.90)),
        "prob_positive": float((net_wk > 0).mean()),
    }


def run_and_export() -> None:
    EXPORT_DB.parent.mkdir(parents=True, exist_ok=True)
    reconcile = verify_three_route_gmv(WAREHOUSE)
    print(f"3-Route GMV Reconciliation PASS: R$ {reconcile['raw_gmv']:,.2f}")

    src = duckdb.connect(WAREHOUSE, read_only=True)
    df = src.execute("SELECT * FROM experiment.exp_outcomes").df()
    t = (df["arm"] == "treatment").to_numpy()
    srm = srm_test({"control": int((~t).sum()), "treatment": int(t.sum())}, {"control": 0.5, "treatment": 0.5})

    y_win = winsorise(df["gmv"].to_numpy(), p=0.99)
    y_cuped, theta = cuped_adjust(y_win, df["pre_gmv"].to_numpy())
    raw_res = welch_test(y_win, t)
    cuped_res = welch_test(y_cuped, t)
    lin_res = lin_estimator(df.assign(gmv_win=y_win), "gmv_win", ["pre_gmv", "pre_orders"])
    vr = variance_reduction(y_win, y_cuped)

    base_mean = float(y_win[~t].mean())
    mde_abs = mde_mean(float(np.std(y_cuped, ddof=1)), int(min(t.sum(), (~t).sum())))
    mde_rel = mde_abs / base_mean
    pwr = achieved_power(y_cuped, t, delta=0.08 * base_mean)

    late_d = ratio_diff(df.loc[t, "late_orders"], df.loc[t, "delivered_orders"],
                        df.loc[~t, "late_orders"], df.loc[~t, "delivered_orders"])
    cancel_d = ratio_diff(df.loc[t, "canceled_orders"], df.loc[t, "all_orders"],
                          df.loc[~t, "canceled_orders"], df.loc[~t, "all_orders"])
    rev_d = ratio_diff(df.loc[t, "review_score_sum"], df.loc[t, "reviewed_orders"],
                       df.loc[~t, "review_score_sum"], df.loc[~t, "reviewed_orders"])
    guardrails = pd.DataFrame([
        {"metric": "late_rate", **non_inferiority_test(late_d["estimate"], late_d["se"], 0.010, "higher")},
        {"metric": "cancel_rate", **non_inferiority_test(cancel_d["estimate"], cancel_d["se"], 0.005, "higher")},
        {"metric": "review_score", **non_inferiority_test(rev_d["estimate"], rev_d["se"], -0.05, "lower")},
    ])

    seg_rows = []
    for seg, g in df.groupby("size_tercile"):
        gt = (g["arm"] == "treatment").to_numpy()
        gy, _ = cuped_adjust(winsorise(g["gmv"].to_numpy(), 0.99), g["pre_gmv"].to_numpy())
        r = welch_test(gy, gt)
        seg_rows.append({"segment": seg, "n": len(g), **r})
    seg_df = pd.DataFrame(seg_rows)
    seg_df["bh_significant"] = benjamini_hochberg(seg_df["p_value"].tolist(), q=0.10)

    any_breach = bool((guardrails["status"] == "BREACH").any())
    if srm["srm_detected"]:
        decision = "BLOCKED_SRM"
    elif cuped_res["ci_lo"] > 0 and not any_breach:
        decision = "ROLL OUT"
    elif cuped_res["ci_hi"] < 0.08 * base_mean:
        decision = "STOP"
    else:
        decision = "EXPAND TARGETED TEST"

    summary_df = pd.DataFrame([
        {"experiment": "fastship_v1", "variant": "Raw Welch (p99)", "srm_p": srm["p_value"],
         "n_per_arm": int(t.sum()), "mde_rel": mde_rel, "power": pwr, "decision": decision, **raw_res},
        {"experiment": "fastship_v1", "variant": "CUPED Welch", "srm_p": srm["p_value"],
         "n_per_arm": int(t.sum()), "mde_rel": mde_rel, "power": pwr, "decision": decision, **cuped_res},
        {"experiment": "fastship_v1", "variant": "Lin's Estimator (HC3)", "srm_p": srm["p_value"],
         "n_per_arm": int(t.sum()), "mde_rel": mde_rel, "power": pwr, "decision": decision, **lin_res},
    ])

    impact = monte_carlo_impact(cuped_res["estimate"] / base_mean, cuped_res["se"] / base_mean, base_mean, len(df))
    strike_df = load_strike_orders(WAREHOUSE)
    did_rob = run_did_robustness(strike_df)
    ev_study = fit_event_study(strike_df)

    out = duckdb.connect(str(EXPORT_DB))
    out.execute("")
    kpi_weekly = src.execute("""
        SELECT week_start, SUM(gmv) AS gmv, SUM(delivered_orders) AS orders,
               SUM(late_orders)*1.0/NULLIF(SUM(delivered_orders),0) AS late_rate
        FROM main_marts.mart_seller_week GROUP BY 1 ORDER BY 1
    """).df()
    cohorts = src.execute("SELECT * FROM main_marts.mart_customer_cohort").df()
    funnel = src.execute("SELECT * FROM main_marts.mart_order_funnel").df()

    for name, frame in [
        ("experiment_summary", summary_df), ("guardrails", guardrails), ("segments", seg_df),
        ("balance", balance_table(df, ["pre_gmv", "pre_orders", "pre_late_rate"])),
        ("did_robustness", did_rob), ("did_event_study", ev_study),
        ("obf_bounds", pd.DataFrame(obrien_fleming_boundaries(6))),
        ("kpi_weekly", kpi_weekly), ("cohorts", cohorts), ("funnel", funnel),
    ]:
        out.register("tmp_df", frame)
        out.execute(f"CREATE OR REPLACE TABLE main.{name} AS SELECT * FROM tmp_df")
    out.close()
    src.close()

    memo_payload = {
        "git_commit": git_commit_hash(),
        "n_eligible_sellers": int(len(df)),
        "decision": decision,
        "srm_p": srm["p_value"],
        "cuped_estimate_brl": cuped_res["estimate"],
        "cuped_ci_brl": [cuped_res["ci_lo"], cuped_res["ci_hi"]],
        "cuped_p_value": cuped_res["p_value"],
        "variance_reduction_pct": round(vr * 100, 2),
        "achieved_mde_rel_pct": round(mde_rel * 100, 2),
        "strike_did_days": float(did_rob.loc[did_rob["check"] == "Main (delivery_days)", "did"].iloc[0]),
        "impact_mc": impact,
    }
    MEMO_JSON.write_text(json.dumps(memo_payload, indent=2))
    print(f"Exported {EXPORT_DB} and {MEMO_JSON}.")
    print(json.dumps(memo_payload, indent=2))


if __name__ == "__main__":
    run_and_export()
