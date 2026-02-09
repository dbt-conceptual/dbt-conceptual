-- Craft version staging model (immutable)
SELECT
    craft_version_code,
    craft_code,
    craft_version_content,
    FALSE AS is_deleted,
    created_at AS load_ts,
    'herd.craft_version' AS rsrc
FROM {{ source('herd', 'craft_version') }}
