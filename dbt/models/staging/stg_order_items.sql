-- grain: 1 row per order line item
SELECT
    order_id,
    CAST(order_item_id AS INTEGER)            AS order_item_id,
    product_id,
    seller_id,
    CAST(shipping_limit_date AS TIMESTAMP)    AS shipping_limit_at,
    CAST(price AS DOUBLE)                     AS price,
    CAST(freight_value AS DOUBLE)             AS freight_value
FROM {{ source('olist_raw', 'order_items') }}
