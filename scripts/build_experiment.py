"""Build semi-synthetic seller-level A/B test tables in DuckDB schema 'experiment'."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
import duckdb
import numpy as np
import pandas as pd

SEED = 20180402
SALT = "fastship_v1"
PRE_START, PRE_END = "2018-01-01", "2018-03-25"
EXP_START, EXP_END = "2018-04-02", "2018-05-13"


def bucket(unit_id: str, salt: str = SALT, n_buckets: int = 1000) -> int:
    h = hashlib.sha256(f"{salt}:{unit_id}".encode()).hexdigest()
    return int(h[:8], 16) % n_buckets


def assign_arm(unit_id: str, salt: str = SALT) -> str:
    return "treatment" if bucket(unit_id, salt) < 500 else "control"


def build_experiment(db_path: str = "data/warehouse/olist.duckdb") -> None:
    rng = np.random.default_rng(SEED)
    con = duckdb.connect(db_path)
    con.execute("CREATE SCHEMA IF NOT EXISTS experiment;")

    eligible = con.execute(f"""
        WITH pre AS (
            SELECT
                seller_key,
                SUM(gmv) AS pre_gmv,
                SUM(delivered_orders) AS pre_orders,
                SUM(late_orders) * 1.0 / NULLIF(SUM(delivered_orders), 0) AS pre_late_rate,
                SUM(canceled_orders) * 1.0 / NULLIF(SUM(all_orders), 0) AS pre_cancel_rate,
                COUNT(*) FILTER (WHERE week_start >= DATE '2018-02-26' AND delivered_orders > 0) AS active_w4
            FROM main_marts.mart_seller_week
            WHERE week_start BETWEEN DATE '{PRE_START}' AND DATE '{PRE_END}'
            GROUP BY 1
        )
        SELECT
            p.seller_key, p.pre_gmv, p.pre_orders,
            COALESCE(p.pre_late_rate, 0.0) AS pre_late_rate,
            COALESCE(p.pre_cancel_rate, 0.0) AS pre_cancel_rate,
            s.seller_state,
            CASE NTILE(3) OVER (ORDER BY p.pre_gmv)
                WHEN 1 THEN 'small' WHEN 2 THEN 'mid' ELSE 'large'
            END AS size_tercile
        FROM pre p
        JOIN main_marts.dim_seller s USING (seller_key)
        WHERE p.pre_orders >= 5 AND p.active_w4 >= 1
    """).df()

    assigned_at = datetime.now(timezone.utc).isoformat()
    assignment = pd.DataFrame({
        "seller_key": eligible["seller_key"],
        "arm": eligible["seller_key"].map(assign_arm),
        "bucket_hash": eligible["seller_key"].map(bucket),
        "salt": SALT,
        "seed": SEED,
        "assigned_at": assigned_at,
    })

    outcomes0 = con.execute(f"""
        SELECT
            seller_key,
            SUM(gmv) AS gmv_0,
            SUM(delivered_orders) AS delivered_orders_0,
            SUM(all_orders) AS all_orders_0,
            SUM(canceled_orders) AS canceled_orders_0,
            SUM(late_orders) AS late_orders_0,
            SUM(reviewed_orders) AS reviewed_orders_0,
            SUM(good_reviews) AS good_reviews_0,
            SUM(review_score_sum) AS review_score_sum_0
        FROM main_marts.mart_seller_week
        WHERE week_start BETWEEN DATE '{EXP_START}' AND DATE '{EXP_END}'
        GROUP BY 1
    """).df()

    df = eligible.merge(assignment[["seller_key", "arm"]], on="seller_key").merge(
        outcomes0, on="seller_key", how="left"
    )
    zero_cols = [c for c in outcomes0.columns if c != "seller_key"]
    df[zero_cols] = df[zero_cols].fillna(0)

    is_t = (df["arm"] == "treatment").to_numpy()
    base_lift = df["size_tercile"].map({"small": 0.12, "mid": 0.04, "large": 0.00}).to_numpy()
    noise = rng.normal(0.0, 0.03, len(df))
    pot_gmv_eff = df["gmv_0"].to_numpy() * (base_lift + noise)
    pot_ord_eff = np.round(df["delivered_orders_0"].to_numpy() * (base_lift * 0.85)).astype(int)
    pot_late_shift = np.where(df["size_tercile"] == "large", 0.015, 0.0)
    pot_cancel_shift = np.where(df["size_tercile"] == "large", 0.007, 0.0)
    pot_rev_shift = np.where(df["size_tercile"] == "large", -0.08, 0.02)

    df["gmv"] = np.maximum(0.0, df["gmv_0"] + np.where(is_t, pot_gmv_eff, 0.0))
    df["delivered_orders"] = np.maximum(0, df["delivered_orders_0"] + np.where(is_t, pot_ord_eff, 0))
    df["all_orders"] = np.maximum(df["delivered_orders"], df["all_orders_0"] + np.where(is_t, pot_ord_eff, 0))
    df["late_orders"] = np.clip(
        df["late_orders_0"] + np.where(is_t, np.round(df["delivered_orders"] * pot_late_shift), 0),
        0, df["delivered_orders"]
    )
    df["canceled_orders"] = np.clip(
        df["canceled_orders_0"] + np.where(is_t, np.round(df["all_orders"] * pot_cancel_shift), 0),
        0, df["all_orders"]
    )
    df["reviewed_orders"] = df["reviewed_orders_0"]
    df["review_score_sum"] = np.clip(
        df["review_score_sum_0"] + np.where(is_t, df["reviewed_orders"] * pot_rev_shift, 0.0),
        df["reviewed_orders"] * 1.0, df["reviewed_orders"] * 5.0
    )
    df["good_reviews"] = np.clip(
        df["good_reviews_0"] + np.where(is_t & (df["size_tercile"] == "large"), -np.round(0.02 * df["reviewed_orders"]), 0),
        0, df["reviewed_orders"]
    )

    truth = pd.DataFrame({
        "seller_key": df["seller_key"],
        "size_tercile": df["size_tercile"],
        "true_effect_gmv": pot_gmv_eff,
        "true_effect_late": pot_late_shift,
        "true_effect_cancel": pot_cancel_shift,
    })

    out_cols = [
        "seller_key", "arm", "pre_gmv", "pre_orders", "pre_late_rate", "seller_state", "size_tercile",
        "gmv", "delivered_orders", "all_orders", "late_orders", "canceled_orders",
        "reviewed_orders", "good_reviews", "review_score_sum",
    ]
    con.register("v_elig", eligible); con.execute("CREATE OR REPLACE TABLE experiment.exp_seller_eligible AS SELECT * FROM v_elig")
    con.register("v_assn", assignment); con.execute("CREATE OR REPLACE TABLE experiment.exp_assignment AS SELECT * FROM v_assn")
    con.register("v_out", df[out_cols]); con.execute("CREATE OR REPLACE TABLE experiment.exp_outcomes AS SELECT * FROM v_out")
    con.register("v_truth", truth); con.execute("CREATE OR REPLACE TABLE experiment.exp_truth AS SELECT * FROM v_truth")
    con.close()
    print(f"Built experiment tables for {len(df)} eligible sellers (T={int(is_t.sum())}, C={int((~is_t).sum())}).")


if __name__ == "__main__":
    build_experiment()
