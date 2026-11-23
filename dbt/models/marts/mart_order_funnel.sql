SELECT
    customer_state,
    COUNT(*)                                                        AS created,
    COUNT(approved_at)                                              AS approved,
    COUNT(shipped_at)                                               AS shipped,
    COUNT(delivered_at)                                             AS delivered,
    COUNT(review_score)                                             AS reviewed,
    MEDIAN(DATE_DIFF('hour', purchased_at, approved_at))            AS med_hours_to_approve,
    MEDIAN(DATE_DIFF('day', approved_at, shipped_at))               AS med_days_dispatch,
    MEDIAN(DATE_DIFF('day', shipped_at, delivered_at))              AS med_days_carrier
FROM {{ ref('int_orders_enriched') }}
GROUP BY 1
