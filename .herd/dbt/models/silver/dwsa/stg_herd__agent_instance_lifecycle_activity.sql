-- Agent instance lifecycle activity staging model (insert-only)
SELECT
    agent_instance_code,
    lifecycle_event_type,
    lifecycle_detail,
    FALSE AS is_deleted,
    created_at AS load_ts,
    'herd.agent_instance_lifecycle_activity' AS rsrc
FROM {{ source('herd', 'agent_instance_lifecycle_activity') }}
