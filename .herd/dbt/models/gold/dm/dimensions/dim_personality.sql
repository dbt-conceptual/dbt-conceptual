-- Dimension: Personality (Type 1)
-- Grain: one row per personality (current state only)
-- TK aliased as SK

SELECT
    h.personality_tk AS personality_sk,
    h.personality_code,
    s.personality_description,
    s.is_deleted
FROM {{ ref('h_personality') }} h
JOIN {{ ref('s_personality_base') }} s
    ON h.personality_tk = s.personality_tk
QUALIFY ROW_NUMBER() OVER (PARTITION BY h.personality_tk ORDER BY s.load_ts DESC) = 1
