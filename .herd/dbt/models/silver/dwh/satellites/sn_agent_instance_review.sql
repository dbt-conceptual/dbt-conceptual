-- Non-historized Satellite: Agent instance review activity (append-only)
-- materialized='incremental', no hashdiff, no dedup

SELECT
    SHA1(LOWER(CONCAT_WS('|', ai.agent_code, air.agent_instance_code))) AS agent_instance_tk,
    {{ generate_hash('ai.agent_code') }} AS agent_tk,
    {{ generate_hash('air.review_code') }} AS review_tk,
    {{ generate_hash('air.pr_code') }} AS pull_request_tk,
    air.agent_instance_code,
    air.review_code,
    air.pr_code,
    air.review_event_type,
    air.review_finding_code,
    air.review_activity_detail,
    air.load_ts,
    air.rsrc
FROM {{ ref('stg_herd__agent_instance_review_activity') }} air
JOIN {{ ref('stg_herd__agent_instance') }} ai
    ON air.agent_instance_code = ai.agent_instance_code
{% if is_incremental() %}
WHERE air.load_ts > (SELECT COALESCE(MAX(load_ts), '1900-01-01') FROM {{ this }})
{% endif %}
