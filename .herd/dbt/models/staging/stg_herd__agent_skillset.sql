-- Agent skillset junction staging model
SELECT
    agent_code,
    skillset_code,
    CASE WHEN deleted_at IS NOT NULL THEN TRUE ELSE FALSE END AS is_deleted,
    created_at AS load_ts,
    'herd.agent_skillset' AS rsrc
FROM {{ source('herd', 'agent_skillset') }}
