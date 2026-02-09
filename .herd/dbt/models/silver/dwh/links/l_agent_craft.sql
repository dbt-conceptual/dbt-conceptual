-- Standing Link: Agent uses a craft
-- materialized='incremental', unique_key='agent_craft_tk'

SELECT
    SHA1(LOWER(CONCAT_WS('|', ai.agent_code, cv.craft_code))) AS agent_craft_tk,
    {{ generate_hash('ai.agent_code') }} AS agent_tk,
    {{ generate_hash('cv.craft_code') }} AS craft_tk,
    MIN(ai.agent_instance_started_at) AS load_ts,
    'herd.agent_instance' AS rsrc
FROM {{ ref('stg_herd__agent_instance') }} ai
JOIN {{ ref('stg_herd__craft_version') }} cv ON ai.craft_version_code = cv.craft_version_code
GROUP BY ai.agent_code, cv.craft_code
{% if is_incremental() %}
HAVING SHA1(LOWER(CONCAT_WS('|', ai.agent_code, cv.craft_code))) NOT IN (SELECT agent_craft_tk FROM {{ this }})
{% endif %}
