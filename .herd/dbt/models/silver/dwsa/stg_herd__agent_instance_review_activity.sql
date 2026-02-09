-- Agent instance review activity staging model (insert-only)
SELECT
    agent_instance_code,
    review_code,
    pr_code,
    review_event_type,
    review_finding_code,
    review_activity_detail,
    FALSE AS is_deleted,
    created_at AS load_ts,
    'herd.agent_instance_review_activity' AS rsrc
FROM {{ source('herd', 'agent_instance_review_activity') }}
