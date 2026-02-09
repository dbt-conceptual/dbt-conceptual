-- Dimension: Sprint (Type 2 SCD)
-- Grain: one row per sprint per version
-- Tracks historical changes to sprint attributes

WITH sprint_history AS (
    SELECT
        h.sprint_tk,
        h.sprint_code,
        s.sprint_title,
        s.sprint_goal,
        s.sprint_started_at,
        s.sprint_planned_end_at,
        s.sprint_actual_end_at,
        s.is_deleted,
        s.load_ts AS valid_from,
        LEAD(s.load_ts) OVER (PARTITION BY h.sprint_tk ORDER BY s.load_ts) AS valid_to
    FROM {{ ref('h_sprint') }} h
    JOIN {{ ref('s_sprint_base') }} s
        ON h.sprint_tk = s.sprint_tk
)

SELECT
    {{ generate_hash(['sprint_tk', 'valid_from']) }} AS sprint_sk,
    sprint_tk,
    sprint_code,
    sprint_title,
    sprint_goal,
    sprint_started_at,
    sprint_planned_end_at,
    sprint_actual_end_at,
    is_deleted,
    valid_from,
    COALESCE(valid_to, CAST('9999-12-31' AS TIMESTAMP)) AS valid_to,
    CASE WHEN valid_to IS NULL THEN TRUE ELSE FALSE END AS is_current
FROM sprint_history
