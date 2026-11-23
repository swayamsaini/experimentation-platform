WITH first_sale AS (
    SELECT seller_id, MIN(CAST(purchased_at AS DATE)) AS first_sale_date
    FROM {{ ref('int_order_items_enriched') }}
    GROUP BY 1
)
SELECT
    {{ dbt_utils.generate_surrogate_key(['s.seller_id']) }} AS seller_key,
    s.seller_id,
    s.seller_state,
    s.seller_city,
    s.seller_zip_prefix,
    g.lat,
    g.lng,
    f.first_sale_date
FROM {{ ref('stg_sellers') }} s
LEFT JOIN {{ ref('stg_geolocation') }} g ON s.seller_zip_prefix = g.zip_prefix
LEFT JOIN first_sale f ON s.seller_id = f.seller_id
