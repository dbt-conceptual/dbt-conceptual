-- Agent instance skillset junction staging model
SELECT
    agent_instance_code,
    skillset_version_code,
    FALSE AS is_deleted,
    CURRENT_TIMESTAMP AS load_ts,
    'herd.agent_instance_skillset' AS rsrc
FROM {{ source('herd', 'agent_instance_skillset') }}
