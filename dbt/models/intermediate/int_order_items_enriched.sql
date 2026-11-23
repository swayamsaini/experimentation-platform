-- grain: 1 row per order line item
SELECT
    oi.order_id,
    oi.order_item_id,
    oi.seller_id,
    oi.product_id,
    o.customer_id,
    o.customer_unique_id,
    o.order_status,
    o.purchased_at,
    o.approved_at,
    o.shipped_at,
    o.delivered_at,
    o.estimated_delivery_at,
    oi.price,
    oi.freight_value,
    o.review_score,
    o.is_late,
    o.is_canceled,
    o.delivery_days,
    o.dispatch_days,
    s.seller_state,
    o.customer_state,
    (s.seller_state <> o.customer_state) AS is_interstate,
    CASE
        WHEN sg.lat IS NOT NULL AND cg.lat IS NOT NULL THEN
            2 * 6371 * ASIN(SQRT(
                POW(SIN(RADIANS(cg.lat - sg.lat) / 2), 2)
                + COS(RADIANS(sg.lat)) * COS(RADIANS(cg.lat))
                * POW(SIN(RADIANS(cg.lng - sg.lng) / 2), 2)
            ))
        ELSE NULL
    END AS distance_km
FROM {{ ref('stg_order_items') }} oi
JOIN {{ ref('int_orders_enriched') }} o ON oi.order_id = o.order_id
JOIN {{ ref('stg_sellers') }} s ON oi.seller_id = s.seller_id
LEFT JOIN {{ ref('stg_geolocation') }} sg ON s.seller_zip_prefix = sg.zip_prefix
LEFT JOIN {{ ref('stg_geolocation') }} cg ON o.customer_zip_prefix = cg.zip_prefix
