-- Non-historized Satellite: Agent instance ticket activity (append-only)
-- materialized='incremental', no hashdiff, no dedup

SELECT
    SHA1(LOWER(CONCAT_WS('|', ai.agent_code, ait.agent_instance_code))) AS agent_instance_tk,
    {{ generate_hash('ai.agent_code') }} AS agent_tk,
    {{ generate_hash('ait.ticket_code') }} AS ticket_tk,
    ait.agent_instance_code,
    ait.ticket_code,
    ait.ticket_event_type,
    ait.ticket_status,
    ait.sprint_code,
    ait.blocker_ticket_code,
    ait.blocker_description,
    ait.handoff_to_agent_code,
    ait.ticket_activity_comment,
    ait.load_ts,
    ait.rsrc
FROM {{ ref('stg_herd__agent_instance_ticket_activity') }} ait
JOIN {{ ref('stg_herd__agent_instance') }} ai
    ON ait.agent_instance_code = ai.agent_instance_code
{% if is_incremental() %}
WHERE ait.load_ts > (SELECT COALESCE(MAX(load_ts), '1900-01-01') FROM {{ this }})
{% endif %}
