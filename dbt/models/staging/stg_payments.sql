-- grain: 1 row per order (aggregated across split payments)
SELECT
    order_id,
    COUNT(*)                                  AS payment_count,
    SUM(CAST(payment_value AS DOUBLE))        AS total_payment_value,
    MAX(CAST(payment_installments AS INT))    AS max_installments,
    MODE(payment_type)                        AS primary_payment_type
FROM {{ source('olist_raw', 'order_payments') }}
GROUP BY 1
