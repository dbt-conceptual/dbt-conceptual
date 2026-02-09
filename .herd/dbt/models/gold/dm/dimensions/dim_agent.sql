-- Dimension: Agent (Type 2 SCD)
-- Grain: one row per agent per version
-- Tracks historical changes to agent attributes

WITH agent_history AS (
    SELECT
        h.agent_tk,
        h.agent_code,
        s.agent_role,
        s.agent_status,
        s.agent_branch_prefix,
        s.agent_email,
        s.default_model_code,
        s.is_deleted,
        s.load_ts AS valid_from,
        LEAD(s.load_ts) OVER (PARTITION BY h.agent_tk ORDER BY s.load_ts) AS valid_to
    FROM {{ ref('h_agent') }} h
    JOIN {{ ref('s_agent_base') }} s
        ON h.agent_tk = s.agent_tk
)

SELECT
    {{ generate_hash(['agent_tk', 'valid_from']) }} AS agent_sk,
    agent_tk,
    agent_code,
    agent_role,
    agent_status,
    agent_branch_prefix,
    agent_email,
    default_model_code,
    is_deleted,
    valid_from,
    COALESCE(valid_to, CAST('9999-12-31' AS TIMESTAMP)) AS valid_to,
    CASE WHEN valid_to IS NULL THEN TRUE ELSE FALSE END AS is_current
FROM agent_history
