-- Non-historized Satellite: Agent instance lifecycle events (append-only)
-- materialized='incremental', no hashdiff, no dedup

SELECT
    SHA1(LOWER(CONCAT_WS('|', ai.agent_code, ail.agent_instance_code))) AS agent_instance_tk,
    {{ generate_hash('ai.agent_code') }} AS agent_tk,
    ail.agent_instance_code,
    ail.lifecycle_event_type,
    ail.lifecycle_detail,
    ail.load_ts,
    ail.rsrc
FROM {{ ref('stg_herd__agent_instance_lifecycle_activity') }} ail
JOIN {{ ref('stg_herd__agent_instance') }} ai
    ON ail.agent_instance_code = ai.agent_instance_code
{% if is_incremental() %}
WHERE ail.load_ts > (SELECT COALESCE(MAX(load_ts), '1900-01-01') FROM {{ this }})
{% endif %}
