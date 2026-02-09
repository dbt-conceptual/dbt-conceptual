-- Personality version staging model (immutable)
SELECT
    personality_version_code,
    personality_code,
    personality_version_content,
    FALSE AS is_deleted,
    created_at AS load_ts,
    'herd.personality_version' AS rsrc
FROM {{ source('herd', 'personality_version') }}
