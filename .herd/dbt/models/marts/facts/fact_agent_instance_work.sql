-- Fact: Agent Instance Work
-- Grain: one row per agent instance
-- Tracks work performed by agent instances with Type 2 SCD dimension joins

WITH agent_instance_base AS (
    SELECT
        ln.agent_instance_tk,
        ln.agent_tk,
        ln.ticket_tk,
        ln.model_tk,
        ln.craft_tk,
        ln.personality_tk,
        ln.agent_instance_code,
        ai.agent_instance_started_at,
        ai.agent_instance_ended_at,
        ai.agent_instance_outcome,
        ai.load_ts
    FROM {{ ref('ln_agent_instance') }} ln
    JOIN {{ ref('stg_herd__agent_instance') }} ai
        ON ln.agent_instance_code = ai.agent_instance_code
),

lifecycle_counts AS (
    SELECT
        agent_instance_tk,
        COUNT(*) AS lifecycle_event_count
    FROM {{ ref('sn_agent_instance_lifecycle') }}
    GROUP BY agent_instance_tk
),

ticket_activity_counts AS (
    SELECT
        agent_instance_tk,
        COUNT(*) AS ticket_activity_count
    FROM {{ ref('sn_agent_instance_ticket') }}
    GROUP BY agent_instance_tk
),

pr_activity_counts AS (
    SELECT
        agent_instance_tk,
        COUNT(*) AS pr_activity_count
    FROM {{ ref('sn_agent_instance_pr') }}
    GROUP BY agent_instance_tk
)

SELECT
    aib.agent_instance_tk,

    -- Type 2 SCD join to dim_agent using valid_from/valid_to
    da.agent_sk,

    -- Type 2 SCD join to dim_ticket using valid_from/valid_to
    dt.ticket_sk,

    -- Type 1 direct join to dim_model
    aib.model_tk AS model_sk,

    -- Type 1 joins to craft and personality
    aib.craft_tk AS craft_sk,
    aib.personality_tk AS personality_sk,

    aib.agent_instance_code,
    aib.agent_instance_started_at,
    aib.agent_instance_ended_at,
    aib.agent_instance_outcome,

    -- Derived measures
    EXTRACT(EPOCH FROM (aib.agent_instance_ended_at - aib.agent_instance_started_at)) / 60.0 AS instance_duration_minutes,

    -- Activity counts
    COALESCE(lc.lifecycle_event_count, 0) AS lifecycle_event_count,
    COALESCE(tac.ticket_activity_count, 0) AS ticket_activity_count,
    COALESCE(pac.pr_activity_count, 0) AS pr_activity_count

FROM agent_instance_base aib

-- Type 2 SCD join: match agent at the time of instance load
LEFT JOIN {{ ref('dim_agent') }} da
    ON aib.agent_tk = da.agent_tk
    AND aib.load_ts >= da.valid_from
    AND aib.load_ts < da.valid_to

-- Type 2 SCD join: match ticket at the time of instance load
LEFT JOIN {{ ref('dim_ticket') }} dt
    ON aib.ticket_tk = dt.ticket_tk
    AND aib.load_ts >= dt.valid_from
    AND aib.load_ts < dt.valid_to

LEFT JOIN lifecycle_counts lc
    ON aib.agent_instance_tk = lc.agent_instance_tk

LEFT JOIN ticket_activity_counts tac
    ON aib.agent_instance_tk = tac.agent_instance_tk

LEFT JOIN pr_activity_counts pac
    ON aib.agent_instance_tk = pac.agent_instance_tk
