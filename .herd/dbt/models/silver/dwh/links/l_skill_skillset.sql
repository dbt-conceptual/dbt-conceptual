-- Standing Link: Decomposes skillset back to individual skills
-- materialized='incremental', unique_key='skill_skillset_tk'

WITH skill_with_combo AS (
    SELECT
        ags.agent_code,
        ags.skillset_code,
        LOWER(CONCAT_WS('|', LIST_VALUE(LIST_SORT(LIST(ags2.skillset_code))))) AS skillset_combination_bk,
        MIN(ags.load_ts) AS first_seen_at
    FROM {{ ref('stg_herd__agent_skillset') }} ags
    JOIN {{ ref('stg_herd__agent_skillset') }} ags2
        ON ags.agent_code = ags2.agent_code
        AND NOT ags2.is_deleted
    WHERE NOT ags.is_deleted
    GROUP BY ags.agent_code, ags.skillset_code
)
SELECT DISTINCT
    SHA1(LOWER(CONCAT_WS('|', swc.skillset_code, swc.skillset_combination_bk))) AS skill_skillset_tk,
    {{ generate_hash('swc.skillset_code') }} AS skill_tk,
    SHA1(swc.skillset_combination_bk) AS skillset_tk,
    swc.first_seen_at AS load_ts,
    'herd.agent_skillset' AS rsrc
FROM skill_with_combo swc
{% if is_incremental() %}
WHERE SHA1(LOWER(CONCAT_WS('|', swc.skillset_code, swc.skillset_combination_bk))) NOT IN (SELECT skill_skillset_tk FROM {{ this }})
{% endif %}
