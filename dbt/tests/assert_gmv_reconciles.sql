WITH raw_total AS (SELECT SUM(CAST(price AS DOUBLE)) AS t FROM {{ source('olist_raw', 'order_items') }}),
     fct_total AS (SELECT SUM(price) AS t FROM {{ ref('fct_order_items') }})
SELECT raw_total.t AS raw_gmv, fct_total.t AS fct_gmv
FROM raw_total, fct_total
WHERE ABS(raw_total.t - fct_total.t) > 0.01
