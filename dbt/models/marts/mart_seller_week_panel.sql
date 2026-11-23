WITH weeks AS (SELECT DISTINCT week_start FROM {{ ref('dim_date') }}),
     sellers AS (SELECT seller_key, seller_state FROM {{ ref('dim_seller') }})
SELECT
    s.seller_key,
    s.seller_state,
    w.week_start,
    COALESCE(m.all_orders, 0)        AS all_orders,
    COALESCE(m.delivered_orders, 0)  AS delivered_orders,
    COALESCE(m.canceled_orders, 0)   AS canceled_orders,
    COALESCE(m.late_orders, 0)       AS late_orders,
    COALESCE(m.reviewed_orders, 0)   AS reviewed_orders,
    COALESCE(m.good_reviews, 0)      AS good_reviews,
    COALESCE(m.review_score_sum, 0)  AS review_score_sum,
    COALESCE(m.gmv, 0.0)             AS gmv,
    m.late_rate,
    m.cancel_rate,
    m.good_review_share,
    m.mean_review_score
FROM sellers s
CROSS JOIN weeks w
LEFT JOIN {{ ref('mart_seller_week') }} m USING (seller_key, week_start)
