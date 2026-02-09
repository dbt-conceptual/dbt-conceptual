-- Personality definitions staging model
SELECT
    personality_code,
    personality_description,
    CASE WHEN deleted_at IS NOT NULL THEN TRUE ELSE FALSE END AS is_deleted,
    COALESCE(modified_at, created_at) AS load_ts,
    'herd.personality_def' AS rsrc
FROM {{ source('herd', 'personality_def') }}
