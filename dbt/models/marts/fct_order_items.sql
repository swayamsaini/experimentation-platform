-- grain: 1 row per order line item
SELECT
    {{ dbt_utils.generate_surrogate_key(['order_id', 'order_item_id']) }} AS order_item_key,
    order_id,
    order_item_id,
    {{ dbt_utils.generate_surrogate_key(['seller_id']) }}                 AS seller_key,
    {{ dbt_utils.generate_surrogate_key(['customer_unique_id']) }}        AS customer_key,
    {{ dbt_utils.generate_surrogate_key(['product_id']) }}                AS product_key,
    CAST(purchased_at AS DATE)                                            AS date_key,
    order_status,
    price,
    freight_value,
    review_score,
    is_late,
    is_canceled,
    delivery_days,
    dispatch_days,
    is_interstate,
    distance_km
FROM {{ ref('int_order_items_enriched') }}
