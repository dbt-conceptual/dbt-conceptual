-- Skillset version staging model (immutable)
SELECT
    skillset_version_code,
    skillset_code,
    skillset_version_content,
    FALSE AS is_deleted,
    created_at AS load_ts,
    'herd.skillset_version' AS rsrc
FROM {{ source('herd', 'skillset_version') }}
