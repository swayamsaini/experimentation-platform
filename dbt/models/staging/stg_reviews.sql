-- grain: 1 row per order (latest review wins)
WITH ranked AS (
    SELECT
        order_id,
        review_id,
        CAST(review_score AS INTEGER)             AS review_score,
        CAST(review_creation_date AS TIMESTAMP)   AS review_created_at,
        ROW_NUMBER() OVER (
            PARTITION BY order_id
            ORDER BY CAST(review_creation_date AS TIMESTAMP) DESC, review_id DESC
        ) AS rn
    FROM {{ source('olist_raw', 'order_reviews') }}
)
SELECT order_id, review_id, review_score, review_created_at
FROM ranked
WHERE rn = 1
