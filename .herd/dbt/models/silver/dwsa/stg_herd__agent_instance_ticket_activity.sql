-- Agent instance ticket activity staging model (insert-only)
SELECT
    agent_instance_code,
    ticket_code,
    ticket_event_type,
    ticket_status,
    sprint_code,
    blocker_ticket_code,
    blocker_description,
    handoff_to_agent_code,
    ticket_activity_comment,
    FALSE AS is_deleted,
    created_at AS load_ts,
    'herd.agent_instance_ticket_activity' AS rsrc
FROM {{ source('herd', 'agent_instance_ticket_activity') }}
