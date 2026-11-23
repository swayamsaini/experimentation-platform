-- grain: 1 row per Portuguese category
SELECT
    TRIM(product_category_name)          AS category_pt,
    TRIM(product_category_name_english)  AS category_en
FROM {{ source('olist_raw', 'category_translation') }}
