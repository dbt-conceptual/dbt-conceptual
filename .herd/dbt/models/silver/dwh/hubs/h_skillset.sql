-- Hub: Skillset business key (constructed entity - unique combination of skills assigned to an agent)
-- materialized='incremental', unique_key='skillset_tk'

WITH agent_skill_combinations AS (
    SELECT
        agent_code,
        LOWER(CONCAT_WS('|', LIST_VALUE(LIST_SORT(LIST(skillset_code))))) AS skillset_combination_bk,
        MIN(load_ts) AS first_seen_at
    FROM {{ ref('stg_herd__agent_skillset') }}
    WHERE NOT is_deleted
    GROUP BY agent_code
)
SELECT
    SHA1(skillset_combination_bk) AS skillset_tk,
    skillset_combination_bk AS skillset_code,
    first_seen_at AS load_ts,
    'herd.agent_skillset' AS rsrc
FROM agent_skill_combinations
{% if is_incremental() %}
WHERE SHA1(skillset_combination_bk) NOT IN (SELECT skillset_tk FROM {{ this }})
{% endif %}
