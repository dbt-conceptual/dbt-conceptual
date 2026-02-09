-- Initiative definitions staging model
SELECT
    initiative_code,
    initiative_title,
    initiative_description,
    initiative_status,
    CASE WHEN deleted_at IS NOT NULL THEN TRUE ELSE FALSE END AS is_deleted,
    COALESCE(modified_at, created_at) AS load_ts,
    'herd.initiative_def' AS rsrc
FROM {{ source('herd', 'initiative_def') }}
