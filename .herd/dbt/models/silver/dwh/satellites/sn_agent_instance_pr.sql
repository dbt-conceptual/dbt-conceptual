-- Non-historized Satellite: Agent instance PR activity (append-only)
-- materialized='incremental', no hashdiff, no dedup

SELECT
    SHA1(LOWER(CONCAT_WS('|', ai.agent_code, aip.agent_instance_code))) AS agent_instance_tk,
    {{ generate_hash('ai.agent_code') }} AS agent_tk,
    {{ generate_hash('aip.pr_code') }} AS pull_request_tk,
    aip.agent_instance_code,
    aip.pr_code,
    aip.pr_event_type,
    aip.pr_commit_hash,
    aip.pr_push_lines_added,
    aip.pr_push_lines_deleted,
    aip.pr_activity_detail,
    aip.load_ts,
    aip.rsrc
FROM {{ ref('stg_herd__agent_instance_pr_activity') }} aip
JOIN {{ ref('stg_herd__agent_instance') }} ai
    ON aip.agent_instance_code = ai.agent_instance_code
{% if is_incremental() %}
WHERE aip.load_ts > (SELECT COALESCE(MAX(load_ts), '1900-01-01') FROM {{ this }})
{% endif %}
