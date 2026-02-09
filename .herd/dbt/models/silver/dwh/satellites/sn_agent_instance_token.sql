-- Non-historized Satellite: Agent instance token usage (append-only)
-- materialized='incremental', no hashdiff, no dedup

SELECT
    SHA1(LOWER(CONCAT_WS('|', ai.agent_code, ait.agent_instance_code))) AS agent_instance_tk,
    {{ generate_hash('ai.agent_code') }} AS agent_tk,
    {{ generate_hash('ait.model_code') }} AS model_tk,
    {{ generate_hash('ai.ticket_code') }} AS ticket_tk,
    ait.agent_instance_code,
    ait.model_code,
    ait.token_input_count,
    ait.token_output_count,
    ait.token_cache_read_count,
    ait.token_cache_create_count,
    ait.token_cost_usd,
    ait.token_context_utilization_pct,
    ait.load_ts,
    ait.rsrc
FROM {{ ref('stg_herd__agent_instance_token_activity') }} ait
JOIN {{ ref('stg_herd__agent_instance') }} ai
    ON ait.agent_instance_code = ai.agent_instance_code
{% if is_incremental() %}
WHERE ait.load_ts > (SELECT COALESCE(MAX(load_ts), '1900-01-01') FROM {{ this }})
{% endif %}
