-- Skillset definitions staging model
SELECT
    skillset_code,
    skillset_description,
    CASE WHEN deleted_at IS NOT NULL THEN TRUE ELSE FALSE END AS is_deleted,
    COALESCE(modified_at, created_at) AS load_ts,
    'herd.skillset_def' AS rsrc
FROM {{ source('herd', 'skillset_def') }}
