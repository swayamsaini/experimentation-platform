WITH firsts AS (
    SELECT customer_key, MIN(date_key) AS first_order_date
    FROM {{ ref('fct_order_items') }}
    WHERE order_status = 'delivered'
    GROUP BY 1
), activity AS (
    SELECT
        f.customer_key,
        DATE_TRUNC('month', f.first_order_date)            AS cohort_month,
        DATE_DIFF('month', f.first_order_date, o.date_key) AS month_offset
    FROM firsts f
    JOIN {{ ref('fct_order_items') }} o USING (customer_key)
    WHERE o.order_status = 'delivered'
)
SELECT cohort_month, month_offset, COUNT(DISTINCT customer_key) AS active_customers
FROM activity
GROUP BY 1, 2
