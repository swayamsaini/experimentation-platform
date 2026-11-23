WITH base AS (
    SELECT
        seller_key,
        MAX(date_key) AS last_sale,
        COUNT(DISTINCT order_id) AS orders,
        SUM(price) AS gmv
    FROM {{ ref('fct_order_items') }}
    WHERE order_status = 'delivered' AND date_key <= DATE '2018-03-25'
    GROUP BY 1
)
SELECT
    seller_key,
    last_sale, orders, gmv,
    NTILE(3) OVER (ORDER BY last_sale) AS r_score,
    NTILE(3) OVER (ORDER BY orders)    AS f_score,
    NTILE(3) OVER (ORDER BY gmv)       AS m_score
FROM base
