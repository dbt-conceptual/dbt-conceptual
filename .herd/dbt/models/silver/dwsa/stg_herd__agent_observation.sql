-- Agent observation staging model
SELECT
    observation_id,
    agent_code,
    session_code,
    observation_type,
    observation_content,
    confidence,
    deleted_at IS NOT NULL AS is_deleted,
    created_at AS load_ts,
    'herd.agent_observation' AS rsrc
FROM {{ source('herd', 'agent_observation') }}
