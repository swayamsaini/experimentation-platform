-- grain: 1 row per order
SELECT
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    c.customer_state,
    c.customer_zip_prefix,
    o.order_status,
    o.purchased_at,
    o.approved_at,
    o.shipped_at,
    o.delivered_at,
    o.estimated_delivery_at,
    r.review_score,
    p.total_payment_value,
    p.primary_payment_type,
    CASE
        WHEN o.order_status = 'delivered' AND o.delivered_at IS NOT NULL
             AND o.estimated_delivery_at IS NOT NULL
        THEN (o.delivered_at > o.estimated_delivery_at)
        ELSE NULL
    END AS is_late,
    CASE
        WHEN o.delivered_at IS NOT NULL AND o.delivered_at >= o.purchased_at
        THEN DATE_DIFF('day', o.purchased_at, o.delivered_at)
        ELSE NULL
    END AS delivery_days,
    CASE
        WHEN o.shipped_at IS NOT NULL AND o.approved_at IS NOT NULL
             AND o.shipped_at >= o.approved_at
        THEN DATE_DIFF('hour', o.approved_at, o.shipped_at) / 24.0
        ELSE NULL
    END AS dispatch_days,
    (o.order_status IN ('canceled', 'unavailable')) AS is_canceled
FROM {{ ref('stg_orders') }} o
JOIN {{ ref('stg_customers') }} c ON o.customer_id = c.customer_id
LEFT JOIN {{ ref('stg_reviews') }} r ON o.order_id = r.order_id
LEFT JOIN {{ ref('stg_payments') }} p ON o.order_id = p.order_id
