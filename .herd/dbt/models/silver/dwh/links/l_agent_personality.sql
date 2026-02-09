-- Standing Link: Agent uses a personality
-- materialized='incremental', unique_key='agent_personality_tk'

SELECT
    SHA1(LOWER(CONCAT_WS('|', ai.agent_code, pv.personality_code))) AS agent_personality_tk,
    {{ generate_hash('ai.agent_code') }} AS agent_tk,
    {{ generate_hash('pv.personality_code') }} AS personality_tk,
    MIN(ai.agent_instance_started_at) AS load_ts,
    'herd.agent_instance' AS rsrc
FROM {{ ref('stg_herd__agent_instance') }} ai
JOIN {{ ref('stg_herd__personality_version') }} pv ON ai.personality_version_code = pv.personality_version_code
GROUP BY ai.agent_code, pv.personality_code
{% if is_incremental() %}
HAVING SHA1(LOWER(CONCAT_WS('|', ai.agent_code, pv.personality_code))) NOT IN (SELECT agent_personality_tk FROM {{ this }})
{% endif %}
