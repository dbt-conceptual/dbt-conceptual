-- Fact: Sprint Burndown
-- Grain: one row per ticket per sprint
-- Tracks ticket status progression within sprints

WITH sprint_ticket_activity AS (
    SELECT
        sn.ticket_tk,
        sn.sprint_code,
        sn.ticket_status,
        sn.ticket_event_type,
        sn.load_ts AS event_ts,
        ROW_NUMBER() OVER (PARTITION BY sn.ticket_tk, sn.sprint_code ORDER BY sn.load_ts) AS event_sequence
    FROM {{ ref('sn_agent_instance_ticket') }} sn
    WHERE sn.sprint_code IS NOT NULL
),

ticket_completion AS (
    SELECT
        ticket_tk,
        sprint_code,
        MIN(CASE WHEN ticket_status IN ('done', 'completed', 'closed') THEN event_ts END) AS completed_at
    FROM sprint_ticket_activity
    GROUP BY ticket_tk, sprint_code
)

SELECT
    sta.ticket_tk,

    -- Type 2 SCD join to dim_ticket using valid_from/valid_to
    dt.ticket_sk,

    -- Type 2 SCD join to dim_sprint using valid_from/valid_to
    ds.sprint_sk,

    sta.sprint_code,
    sta.ticket_status,
    sta.ticket_event_type,
    sta.event_ts,
    sta.event_sequence,

    tc.completed_at AS ticket_completed_at

FROM sprint_ticket_activity sta

-- Type 2 SCD join: match ticket at the time of event
LEFT JOIN {{ ref('dim_ticket') }} dt
    ON sta.ticket_tk = dt.ticket_tk
    AND sta.event_ts >= dt.valid_from
    AND sta.event_ts < dt.valid_to

-- Type 2 SCD join: match sprint at the time of event
LEFT JOIN {{ ref('h_sprint') }} hs
    ON sta.sprint_code = hs.sprint_code

LEFT JOIN {{ ref('dim_sprint') }} ds
    ON hs.sprint_tk = ds.sprint_tk
    AND sta.event_ts >= ds.valid_from
    AND sta.event_ts < ds.valid_to

LEFT JOIN ticket_completion tc
    ON sta.ticket_tk = tc.ticket_tk
    AND sta.sprint_code = tc.sprint_code
