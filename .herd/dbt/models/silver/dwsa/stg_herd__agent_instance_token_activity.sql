-- Agent instance token activity staging model (insert-only)
SELECT
    agent_instance_code,
    model_code,
    token_input_count,
    token_output_count,
    token_cache_read_count,
    token_cache_create_count,
    token_cost_usd,
    token_context_utilization_pct,
    FALSE AS is_deleted,
    created_at AS load_ts,
    'herd.agent_instance_token_activity' AS rsrc
FROM {{ source('herd', 'agent_instance_token_activity') }}
