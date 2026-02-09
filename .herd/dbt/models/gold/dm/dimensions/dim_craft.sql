-- Dimension: Craft (Type 1)
-- Grain: one row per craft (current state only)
-- TK aliased as SK

SELECT
    h.craft_tk AS craft_sk,
    h.craft_code,
    s.craft_description,
    s.is_deleted
FROM {{ ref('h_craft') }} h
JOIN {{ ref('s_craft_base') }} s
    ON h.craft_tk = s.craft_tk
QUALIFY ROW_NUMBER() OVER (PARTITION BY h.craft_tk ORDER BY s.load_ts DESC) = 1
