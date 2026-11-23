-- grain: 1 row per product (fixes source 'lenght' typos)
SELECT
    p.product_id,
    COALESCE(t.category_en, p.product_category_name, 'unknown') AS category_en,
    COALESCE(p.product_category_name, 'unknown')                AS category_pt,
    CAST(p.product_name_lenght AS INTEGER)                      AS product_name_length,
    CAST(p.product_description_lenght AS INTEGER)               AS product_description_length,
    CAST(p.product_photos_qty AS INTEGER)                       AS photos_qty,
    CAST(p.product_weight_g AS DOUBLE)                          AS weight_g,
    CAST(p.product_length_cm AS DOUBLE)                         AS length_cm,
    CAST(p.product_height_cm AS DOUBLE)                         AS height_cm,
    CAST(p.product_width_cm AS DOUBLE)                          AS width_cm
FROM {{ source('olist_raw', 'products') }} p
LEFT JOIN {{ ref('stg_category_translation') }} t
    ON p.product_category_name = t.category_pt
