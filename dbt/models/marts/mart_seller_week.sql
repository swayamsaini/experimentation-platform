{{ config(materialized='incremental', unique_key=['seller_key', 'week_start']) }}

WITH item_agg AS (
    SELECT
        seller_key,
        DATE_TRUNC('week', date_key) AS week_start,
        SUM(CASE WHEN order_status = 'delivered' THEN price ELSE 0.0 END)                 AS gmv,
        SUM(CASE WHEN order_status = 'delivered' THEN price + freight_value ELSE 0.0 END) AS gross_with_freight
    FROM {{ ref('fct_order_items') }}
    {% if is_incremental() %}
      WHERE DATE_TRUNC('week', date_key) >= (SELECT MAX(week_start) - INTERVAL 14 DAY FROM {{ this }})
    {% endif %}
    GROUP BY 1, 2
),
seller_orders AS (
    SELECT DISTINCT
        seller_key,
        order_id,
        DATE_TRUNC('week', date_key) AS week_start,
        order_status,
        is_late,
        is_canceled,
        review_score
    FROM {{ ref('fct_order_items') }}
    {% if is_incremental() %}
      WHERE DATE_TRUNC('week', date_key) >= (SELECT MAX(week_start) - INTERVAL 14 DAY FROM {{ this }})
    {% endif %}
),
order_agg AS (
    SELECT
        seller_key,
        week_start,
        COUNT(*)                                                                AS all_orders,
        COUNT(*) FILTER (WHERE order_status = 'delivered')                      AS delivered_orders,
        COUNT(*) FILTER (WHERE is_canceled)                                     AS canceled_orders,
        COUNT(*) FILTER (WHERE order_status = 'delivered' AND is_late)          AS late_orders,
        COUNT(*) FILTER (WHERE order_status = 'delivered' AND review_score IS NOT NULL) AS reviewed_orders,
        COUNT(*) FILTER (WHERE order_status = 'delivered' AND review_score >= 4)        AS good_reviews,
        SUM(CASE WHEN order_status = 'delivered' THEN review_score ELSE 0 END)  AS review_score_sum
    FROM seller_orders
    GROUP BY 1, 2
)
SELECT
    o.seller_key,
    o.week_start,
    o.all_orders,
    o.delivered_orders,
    o.canceled_orders,
    o.late_orders,
    o.reviewed_orders,
    o.good_reviews,
    o.review_score_sum,
    i.gmv,
    i.gross_with_freight,
    i.gmv / NULLIF(o.delivered_orders, 0)                             AS aov,
    CAST(o.late_orders AS DOUBLE) / NULLIF(o.delivered_orders, 0)     AS late_rate,
    CAST(o.canceled_orders AS DOUBLE) / NULLIF(o.all_orders, 0)       AS cancel_rate,
    CAST(o.good_reviews AS DOUBLE) / NULLIF(o.reviewed_orders, 0)     AS good_review_share,
    CAST(o.review_score_sum AS DOUBLE) / NULLIF(o.reviewed_orders, 0) AS mean_review_score
FROM order_agg o
JOIN item_agg i USING (seller_key, week_start)
