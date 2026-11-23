-- grain: 1 row per seller
SELECT
    seller_id,
    LPAD(CAST(seller_zip_code_prefix AS VARCHAR), 5, '0')   AS seller_zip_prefix,
    LOWER(TRIM(seller_city))                                AS seller_city,
    UPPER(TRIM(seller_state))                               AS seller_state
FROM {{ source('olist_raw', 'sellers') }}
