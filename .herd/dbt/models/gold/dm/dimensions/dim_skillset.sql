-- Dimension: Skillset (Type 1)
-- Grain: one row per skillset (current state only)
-- Aggregates skills linked to each skillset

SELECT
    h.skillset_tk AS skillset_sk,
    h.skillset_tk,
    LIST_AGG(DISTINCT hs.skill_code, ', ' ORDER BY hs.skill_code) AS skill_codes
FROM {{ ref('h_skillset') }} h
LEFT JOIN {{ ref('l_skill_skillset') }} l
    ON h.skillset_tk = l.skillset_tk
LEFT JOIN {{ ref('h_skill') }} hs
    ON l.skill_tk = hs.skill_tk
GROUP BY h.skillset_tk
