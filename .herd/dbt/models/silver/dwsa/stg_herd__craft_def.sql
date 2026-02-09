-- Craft definitions staging model
SELECT
    craft_code,
    craft_description,
    CASE WHEN deleted_at IS NOT NULL THEN TRUE ELSE FALSE END AS is_deleted,
    COALESCE(modified_at, created_at) AS load_ts,
    'herd.craft_def' AS rsrc
FROM {{ source('herd', 'craft_def') }}
