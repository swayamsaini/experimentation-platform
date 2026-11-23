WITH raw_n AS (SELECT COUNT(*) AS n FROM {{ source('olist_raw', 'order_items') }}),
     fct_n AS (SELECT COUNT(*) AS n FROM {{ ref('fct_order_items') }})
SELECT * FROM raw_n, fct_n WHERE raw_n.n <> fct_n.n
