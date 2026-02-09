-- Dimension: Project (Type 1)
-- Grain: one row per project (current state only)
-- TK aliased as SK

SELECT
    h.project_tk AS project_sk,
    h.project_code,
    s.initiative_code,
    s.project_title,
    s.project_description,
    s.project_status,
    s.is_deleted
FROM {{ ref('h_project') }} h
JOIN {{ ref('s_project_base') }} s
    ON h.project_tk = s.project_tk
QUALIFY ROW_NUMBER() OVER (PARTITION BY h.project_tk ORDER BY s.load_ts DESC) = 1
