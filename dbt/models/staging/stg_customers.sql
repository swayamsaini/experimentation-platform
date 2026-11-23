-- grain: 1 row per order-scoped customer_id
SELECT
    customer_id,
    customer_unique_id,
    LPAD(CAST(customer_zip_code_prefix AS VARCHAR), 5, '0') AS customer_zip_prefix,
    LOWER(TRIM(customer_city))                              AS customer_city,
    UPPER(TRIM(customer_state))                             AS customer_state
FROM {{ source('olist_raw', 'customers') }}
