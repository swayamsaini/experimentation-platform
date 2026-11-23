SELECT
    {{ dbt_utils.generate_surrogate_key(['product_id']) }} AS product_key,
    product_id,
    category_en,
    category_pt,
    weight_g,
    CASE
        WHEN weight_g IS NULL THEN 'unknown'
        WHEN weight_g < 500 THEN 'light'
        WHEN weight_g < 2000 THEN 'medium'
        ELSE 'heavy'
    END AS weight_bucket
FROM {{ ref('stg_products') }}
