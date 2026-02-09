-- Agent instance PR activity staging model (insert-only)
SELECT
    agent_instance_code,
    pr_code,
    pr_event_type,
    pr_commit_hash,
    pr_push_lines_added,
    pr_push_lines_deleted,
    pr_activity_detail,
    FALSE AS is_deleted,
    created_at AS load_ts,
    'herd.agent_instance_pr_activity' AS rsrc
FROM {{ source('herd', 'agent_instance_pr_activity') }}
