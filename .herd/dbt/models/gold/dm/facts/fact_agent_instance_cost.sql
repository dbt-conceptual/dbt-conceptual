-- Fact: Agent Instance Cost
-- Grain: one row per agent instance (aggregated token usage)
-- Aggregates all token usage for each agent instance

WITH agent_instance_base AS (
    SELECT
        ln.agent_instance_tk,
        ln.agent_tk,
        ln.ticket_tk,
        ln.model_tk,
        ln.agent_instance_code,
        ai.load_ts
    FROM {{ ref('ln_agent_instance') }} ln
    JOIN {{ ref('stg_herd__agent_instance') }} ai
        ON ln.agent_instance_code = ai.agent_instance_code
),

token_aggregates AS (
    SELECT
        agent_instance_tk,
        SUM(token_input_count) AS total_token_input_count,
        SUM(token_output_count) AS total_token_output_count,
        SUM(token_cache_read_count) AS total_token_cache_read_count,
        SUM(token_cache_create_count) AS total_token_cache_create_count,
        SUM(token_cost_usd) AS total_token_cost_usd
    FROM {{ ref('sn_agent_instance_token') }}
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

    aib.agent_instance_code,

    -- Token usage measures
    COALESCE(ta.total_token_input_count, 0) AS total_token_input_count,
    COALESCE(ta.total_token_output_count, 0) AS total_token_output_count,
    COALESCE(ta.total_token_cache_read_count, 0) AS total_token_cache_read_count,
    COALESCE(ta.total_token_cache_create_count, 0) AS total_token_cache_create_count,
    COALESCE(ta.total_token_cost_usd, 0) AS total_token_cost_usd

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

LEFT JOIN token_aggregates ta
    ON aib.agent_instance_tk = ta.agent_instance_tk
