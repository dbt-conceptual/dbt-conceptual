-- Agent instance staging model
SELECT
    agent_instance_code,
    agent_code,
    model_code,
    craft_version_code,
    personality_version_code,
    ticket_code,
    spawned_by_agent_instance_code,
    agent_instance_started_at,
    agent_instance_ended_at,
    agent_instance_outcome,
    FALSE AS is_deleted,
    COALESCE(agent_instance_ended_at, agent_instance_started_at) AS load_ts,
    'herd.agent_instance' AS rsrc
FROM {{ source('herd', 'agent_instance') }}
