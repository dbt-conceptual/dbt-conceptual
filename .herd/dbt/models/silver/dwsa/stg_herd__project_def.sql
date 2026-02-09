-- Project definitions staging model
SELECT
    project_code,
    initiative_code,
    project_title,
    project_description,
    project_status,
    CASE WHEN deleted_at IS NOT NULL THEN TRUE ELSE FALSE END AS is_deleted,
    COALESCE(modified_at, created_at) AS load_ts,
    'herd.project_def' AS rsrc
FROM {{ source('herd', 'project_def') }}
