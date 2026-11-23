-- grain: 1 row per 5-digit zip prefix (eliminates 6x join fan-out)
SELECT
    LPAD(CAST(geolocation_zip_code_prefix AS VARCHAR), 5, '0') AS zip_prefix,
    MEDIAN(CAST(geolocation_lat AS DOUBLE))                    AS lat,
    MEDIAN(CAST(geolocation_lng AS DOUBLE))                    AS lng,
    MODE(UPPER(TRIM(geolocation_state)))                       AS state
FROM {{ source('olist_raw', 'geolocation') }}
GROUP BY 1
