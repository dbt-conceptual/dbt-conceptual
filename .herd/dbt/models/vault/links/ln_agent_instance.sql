-- Transactional Link: Agent instance (central transactional link - all activity satellites hang off this)
-- materialized='incremental', unique_key='agent_instance_tk'

SELECT
    SHA1(LOWER(CONCAT_WS('|', ai.agent_code, ai.agent_instance_code))) AS agent_instance_tk,
    {{ generate_hash('ai.agent_code') }} AS agent_tk,
    {{ generate_hash('ai.model_code') }} AS model_tk,
    {{ generate_hash('ai.ticket_code') }} AS ticket_tk,
    {{ generate_hash('cv.craft_code') }} AS craft_tk,
    {{ generate_hash('pv.personality_code') }} AS personality_tk,
    ai.agent_instance_code,
    ai.craft_version_code,
    ai.personality_version_code,
    ai.spawned_by_agent_instance_code,
    ai.agent_instance_outcome,
    ai.load_ts,
    ai.rsrc
FROM {{ ref('stg_herd__agent_instance') }} ai
LEFT JOIN {{ ref('stg_herd__craft_version') }} cv ON ai.craft_version_code = cv.craft_version_code
LEFT JOIN {{ ref('stg_herd__personality_version') }} pv ON ai.personality_version_code = pv.personality_version_code
{% if is_incremental() %}
WHERE SHA1(LOWER(CONCAT_WS('|', ai.agent_code, ai.agent_instance_code))) NOT IN (SELECT agent_instance_tk FROM {{ this }})
{% endif %}
