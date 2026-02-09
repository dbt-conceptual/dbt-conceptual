-- Standing Link: Agent has a skillset (constructed combination)
-- materialized='incremental', unique_key='agent_skillset_tk'

WITH agent_combinations AS (
    SELECT
        agent_code,
        LOWER(CONCAT_WS('|', LIST_VALUE(LIST_SORT(LIST(skillset_code))))) AS skillset_combination_bk,
        MIN(load_ts) AS first_seen_at
    FROM {{ ref('stg_herd__agent_skillset') }}
    WHERE NOT is_deleted
    GROUP BY agent_code
)
SELECT
    SHA1(LOWER(CONCAT_WS('|', ac.agent_code, ac.skillset_combination_bk))) AS agent_skillset_tk,
    {{ generate_hash('ac.agent_code') }} AS agent_tk,
    SHA1(ac.skillset_combination_bk) AS skillset_tk,
    ac.first_seen_at AS load_ts,
    'herd.agent_skillset' AS rsrc
FROM agent_combinations ac
{% if is_incremental() %}
WHERE SHA1(LOWER(CONCAT_WS('|', ac.agent_code, ac.skillset_combination_bk))) NOT IN (SELECT agent_skillset_tk FROM {{ this }})
{% endif %}
