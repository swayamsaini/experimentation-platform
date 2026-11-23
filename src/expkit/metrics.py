"""Governed Python Metric Registry & 3-Route GMV Reconciliation."""
from __future__ import annotations

from dataclasses import dataclass
import duckdb
import pandas as pd


@dataclass(frozen=True)
class MetricDef:
    name: str
    numerator: str
    denominator: str | None
    kind: str
    description: str


REGISTRY: dict[str, MetricDef] = {
    "gmv": MetricDef("gmv", "gmv", None, "mean", "Delivered item price per seller"),
    "orders": MetricDef("orders", "delivered_orders", None, "mean", "Delivered orders per seller"),
    "aov": MetricDef("aov", "gmv", "delivered_orders", "ratio", "GMV per delivered order"),
    "late_rate": MetricDef("late_rate", "late_orders", "delivered_orders", "ratio", "Late / delivered orders"),
    "cancel_rate": MetricDef("cancel_rate", "canceled_orders", "all_orders", "ratio", "Canceled / all orders"),
    "good_review_share": MetricDef("good_review_share", "good_reviews", "reviewed_orders", "ratio", "4-5 star share"),
    "review_score": MetricDef("review_score", "review_score_sum", "reviewed_orders", "ratio", "Mean review score"),
}


def compute_metric(df: pd.DataFrame, metric_name: str) -> float:
    m = REGISTRY[metric_name]
    if m.denominator is None:
        return float(df[m.numerator].mean())
    denom = float(df[m.denominator].sum())
    return float(df[m.numerator].sum()) / denom if denom > 0 else float("nan")


def verify_three_route_gmv(db_path: str = "data/warehouse/olist.duckdb") -> dict[str, float]:
    con = duckdb.connect(db_path, read_only=True)
    raw_gmv = con.execute("""
        SELECT SUM(CAST(oi.price AS DOUBLE))
        FROM raw.order_items oi
        JOIN raw.orders o ON oi.order_id = o.order_id
        WHERE LOWER(TRIM(o.order_status)) = 'delivered'
    """).fetchone()[0]
    fct_gmv = con.execute(
        "SELECT SUM(price) FROM main_marts.fct_order_items WHERE order_status = 'delivered'"
    ).fetchone()[0]
    mart_gmv = con.execute("SELECT SUM(gmv) FROM main_marts.mart_seller_week").fetchone()[0]
    con.close()
    assert abs(raw_gmv - fct_gmv) < 0.01
    assert abs(raw_gmv - mart_gmv) < 0.01
    return {"raw_gmv": float(raw_gmv), "fct_gmv": float(fct_gmv), "mart_gmv": float(mart_gmv)}
