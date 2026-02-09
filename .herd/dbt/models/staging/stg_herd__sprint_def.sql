-- Sprint definitions staging model
SELECT
    sprint_code,
    sprint_title,
    sprint_goal,
    sprint_started_at,
    sprint_planned_end_at,
    sprint_actual_end_at,
    CASE WHEN deleted_at IS NOT NULL THEN TRUE ELSE FALSE END AS is_deleted,
    COALESCE(modified_at, created_at) AS load_ts,
    'herd.sprint_def' AS rsrc
FROM {{ source('herd', 'sprint_def') }}
