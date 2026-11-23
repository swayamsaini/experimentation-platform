"""Fixed DiD, Event Study & Robustness Suite on the May 2018 Brazilian Truckers' Strike."""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

STRIKE_START = pd.Timestamp("2018-05-21")


def load_strike_orders(db_path: str = "data/warehouse/olist.duckdb") -> pd.DataFrame:
    con = duckdb.connect(db_path, read_only=True)
    df = con.execute("""
        WITH order_seller AS (
            SELECT
                order_id,
                ANY_VALUE(seller_id) AS seller_id,
                ANY_VALUE(seller_state) AS seller_state,
                ANY_VALUE(customer_state) AS customer_state,
                MAX(CAST(is_interstate AS INT)) AS treated,
                MAX(distance_km) AS distance_km,
                AVG(delivery_days) AS delivery_days,
                MAX(CAST(is_late AS INT)) AS is_late,
                AVG(review_score) AS review_score,
                MIN(CAST(purchased_at AS DATE)) AS purchase_date,
                DATE_DIFF('hour', MIN(purchased_at), MIN(approved_at)) AS approval_hours
            FROM main_intermediate.int_order_items_enriched
            WHERE order_status = 'delivered'
              AND delivery_days IS NOT NULL
              AND CAST(purchased_at AS DATE) BETWEEN DATE '2018-03-19' AND DATE '2018-06-17'
            GROUP BY 1
        )
        SELECT *, DATE_TRUNC('week', purchase_date) AS week_start
        FROM order_seller
    """).df()
    con.close()
    df["purchase_date"] = pd.to_datetime(df["purchase_date"])
    df["week_start"] = pd.to_datetime(df["week_start"])
    df["post"] = ((df["purchase_date"] >= "2018-05-14") & (df["purchase_date"] <= "2018-05-31")).astype(int)
    df["seller_code"] = pd.Categorical(df["seller_id"]).codes
    df["week_str"] = df["week_start"].dt.strftime("%Y-%m-%d")
    return df


def fit_did(df: pd.DataFrame, outcome: str = "delivery_days") -> dict:
    m = smf.ols(
        f"{outcome} ~ treated * post + C(seller_state) + C(week_str)", data=df
    ).fit(cov_type="cluster", cov_kwds={"groups": df["seller_code"]})
    ci = m.conf_int().loc["treated:post"]
    return {
        "outcome": outcome,
        "did": float(m.params["treated:post"]),
        "se": float(m.bse["treated:post"]),
        "ci_lo": float(ci[0]),
        "ci_hi": float(ci[1]),
        "p_value": float(m.pvalues["treated:post"]),
        "n": int(len(df)),
    }


def fit_event_study(df: pd.DataFrame, outcome: str = "delivery_days") -> pd.DataFrame:
    work = df.copy()
    work["rel_week"] = ((work["week_start"] - STRIKE_START).dt.days // 7).clip(-8, 4)
    m = smf.ols(
        f"{outcome} ~ treated + C(rel_week, Treatment(reference=-2)):treated + C(rel_week) + C(seller_state)",
        data=work,
    ).fit(cov_type="cluster", cov_kwds={"groups": work["seller_code"]})
    rows = []
    for k in range(-8, 5):
        if k == -2:
            rows.append({"rel_week": k, "coef": 0.0, "ci_lo": 0.0, "ci_hi": 0.0})
            continue
        key = f"C(rel_week, Treatment(reference=-2))[T.{k}]:treated"
        if key in m.params:
            ci = m.conf_int().loc[key]
            rows.append({"rel_week": k, "coef": float(m.params[key]), "ci_lo": float(ci[0]), "ci_hi": float(ci[1])})
    return pd.DataFrame(rows)


def run_did_robustness(df: pd.DataFrame) -> pd.DataFrame:
    results = [
        {"check": "Main (delivery_days)", **fit_did(df, "delivery_days")},
        {"check": "Secondary (is_late)", **fit_did(df, "is_late")},
        {"check": "Secondary (review_score)", **fit_did(df.dropna(subset=["review_score"]), "review_score")},
    ]
    pre_only = df[df["purchase_date"] < "2018-05-14"].copy()
    pre_only["post"] = ((pre_only["purchase_date"] >= "2018-04-02") & (pre_only["purchase_date"] <= "2018-04-19")).astype(int)
    results.append({"check": "Placebo in time (-6w)", **fit_did(pre_only, "delivery_days")})
    results.append({"check": "Placebo outcome (approval_hours)", **fit_did(df.dropna(subset=["approval_hours"]), "approval_hours")})
    log_df = df.copy()
    log_df["log_delivery"] = np.log1p(log_df["delivery_days"])
    results.append({"check": "Log(1 + delivery_days)", **fit_did(log_df, "log_delivery")})
    return pd.DataFrame(results)
