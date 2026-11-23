SELECT * FROM (VALUES
    ('created',     FALSE, FALSE, 1),
    ('approved',    FALSE, FALSE, 2),
    ('invoiced',    FALSE, FALSE, 3),
    ('processing',  FALSE, FALSE, 4),
    ('shipped',     FALSE, FALSE, 5),
    ('delivered',   TRUE,  TRUE,  6),
    ('canceled',    TRUE,  FALSE, 7),
    ('unavailable', TRUE,  FALSE, 8)
) AS t(order_status, is_terminal, is_delivered, funnel_rank)
