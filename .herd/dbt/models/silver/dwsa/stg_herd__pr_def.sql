-- Pull request definitions staging model
SELECT
    pr_code,
    ticket_code,
    creator_agent_instance_code,
    pr_branch_name,
    pr_title,
    pr_lines_added,
    pr_lines_deleted,
    pr_files_changed,
    pr_merged_at,
    pr_closed_at,
    CASE WHEN deleted_at IS NOT NULL THEN TRUE ELSE FALSE END AS is_deleted,
    COALESCE(modified_at, created_at) AS load_ts,
    'herd.pr_def' AS rsrc
FROM {{ source('herd', 'pr_def') }}
