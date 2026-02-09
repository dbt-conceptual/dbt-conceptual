-- Fact: Ticket Lifecycle
-- Grain: one row per ticket status change
-- Tracks ticket status progression and timing

WITH ticket_events AS (
    SELECT
        sn.agent_instance_tk,
        sn.agent_tk,
        sn.ticket_tk,
        sn.ticket_code,
        sn.ticket_event_type,
        sn.ticket_status,
        sn.sprint_code,
        sn.blocker_ticket_code,
        sn.load_ts,
        LAG(sn.ticket_status) OVER (PARTITION BY sn.ticket_tk ORDER BY sn.load_ts) AS previous_status,
        LAG(sn.load_ts) OVER (PARTITION BY sn.ticket_tk ORDER BY sn.load_ts) AS previous_status_ts
    FROM {{ ref('sn_agent_instance_ticket') }} sn
),

agent_instance_info AS (
    SELECT
        ln.agent_instance_tk,
        ln.agent_tk,
        ai.load_ts
    FROM {{ ref('ln_agent_instance') }} ln
    JOIN {{ ref('stg_herd__agent_instance') }} ai
        ON ln.agent_instance_code = ai.agent_instance_code
)

SELECT
    te.agent_instance_tk,

    -- Type 2 SCD join to dim_ticket using valid_from/valid_to
    dt.ticket_sk,

    -- Type 2 SCD join to dim_agent using valid_from/valid_to
    da.agent_sk,

    te.ticket_code,
    te.ticket_event_type,
    te.ticket_status,
    te.previous_status,
    te.sprint_code,
    te.blocker_ticket_code,
    te.load_ts AS event_ts,

    -- Derived measure: time in previous status (minutes)
    CASE
        WHEN te.previous_status_ts IS NOT NULL
        THEN EXTRACT(EPOCH FROM (te.load_ts - te.previous_status_ts)) / 60.0
        ELSE NULL
    END AS time_in_previous_status_minutes

FROM ticket_events te

-- Type 2 SCD join: match ticket at the time of event
LEFT JOIN {{ ref('dim_ticket') }} dt
    ON te.ticket_tk = dt.ticket_tk
    AND te.load_ts >= dt.valid_from
    AND te.load_ts < dt.valid_to

-- Type 2 SCD join: match agent at the time of event
LEFT JOIN agent_instance_info aii
    ON te.agent_instance_tk = aii.agent_instance_tk

LEFT JOIN {{ ref('dim_agent') }} da
    ON aii.agent_tk = da.agent_tk
    AND aii.load_ts >= da.valid_from
    AND aii.load_ts < da.valid_to
