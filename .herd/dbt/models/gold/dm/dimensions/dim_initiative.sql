-- Dimension: Initiative (Type 1)
-- Grain: one row per initiative (current state only)
-- TK aliased as SK

SELECT
    h.initiative_tk AS initiative_sk,
    h.initiative_code,
    s.initiative_title,
    s.initiative_description,
    s.initiative_status,
    s.is_deleted
FROM {{ ref('h_initiative') }} h
JOIN {{ ref('s_initiative_base') }} s
    ON h.initiative_tk = s.initiative_tk
QUALIFY ROW_NUMBER() OVER (PARTITION BY h.initiative_tk ORDER BY s.load_ts DESC) = 1
