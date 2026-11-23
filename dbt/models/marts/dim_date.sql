WITH spine AS (
    SELECT CAST(range AS DATE) AS date_key
    FROM RANGE(DATE '2016-09-01', DATE '2018-11-01', INTERVAL 1 DAY)
)
SELECT
    date_key,
    DATE_TRUNC('week', date_key)                              AS week_start,
    DATE_TRUNC('month', date_key)                             AS month_start,
    EXTRACT(DOW FROM date_key)                                AS day_of_week,
    (date_key = DATE '2017-11-24')                            AS is_black_friday,
    (date_key BETWEEN DATE '2018-05-21' AND DATE '2018-05-31') AS is_truckers_strike
FROM spine
