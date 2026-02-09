-- Agent definitions staging model
SELECT
    agent_code,
    agent_role,
    agent_status,
    agent_branch_prefix,
    agent_email,
    default_model_code,
    CASE WHEN deleted_at IS NOT NULL THEN TRUE ELSE FALSE END AS is_deleted,
    COALESCE(modified_at, created_at) AS load_ts,
    'herd.agent_def' AS rsrc
FROM {{ source('herd', 'agent_def') }}
