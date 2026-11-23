WITH first_ord AS (
    SELECT
        customer_unique_id,
        MIN(CAST(purchased_at AS DATE)) AS first_order_date,
        MODE(customer_state)            AS customer_state,
        MODE(customer_zip_prefix)       AS customer_zip_prefix
    FROM {{ ref('int_orders_enriched') }}
    GROUP BY 1
)
SELECT
    {{ dbt_utils.generate_surrogate_key(['f.customer_unique_id']) }} AS customer_key,
    f.customer_unique_id,
    f.customer_state,
    f.first_order_date,
    g.lat,
    g.lng
FROM first_ord f
LEFT JOIN {{ ref('stg_geolocation') }} g ON f.customer_zip_prefix = g.zip_prefix
