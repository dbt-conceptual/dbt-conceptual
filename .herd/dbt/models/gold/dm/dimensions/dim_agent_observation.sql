-- Dimension: Agent Observation
-- Type 2 SCD with valid_from/valid_to
-- Tracks agent reflexive observations and self-awareness

WITH observation_history AS (
    SELECT
        ob.observation_tk,
        ob.observation_id,
        sat.agent_code,
        sat.session_code,
        sat.observation_type,
        sat.observation_content,
        sat.confidence,
        sat.is_deleted,
        sat.load_ts AS valid_from,
        LEAD(sat.load_ts) OVER (PARTITION BY ob.observation_tk ORDER BY sat.load_ts) AS valid_to
    FROM {{ ref('h_observation') }} ob
    INNER JOIN {{ ref('s_observation_base') }} sat
        ON ob.observation_tk = sat.observation_tk
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['observation_tk', 'valid_from']) }} AS observation_sk,
    observation_tk,
    observation_id,
    agent_code,
    session_code,
    observation_type,
    observation_content,
    confidence,
    is_deleted,
    valid_from,
    COALESCE(valid_to, '9999-12-31'::TIMESTAMP) AS valid_to,
    CASE WHEN valid_to IS NULL THEN TRUE ELSE FALSE END AS is_current
FROM observation_history
