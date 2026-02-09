-- Model definitions staging model
SELECT
    model_code,
    model_provider,
    model_context_window,
    model_input_cost_per_m,
    model_output_cost_per_m,
    model_cache_read_cost_per_m,
    model_cache_create_cost_per_m,
    CASE WHEN deleted_at IS NOT NULL THEN TRUE ELSE FALSE END AS is_deleted,
    COALESCE(modified_at, created_at) AS load_ts,
    'herd.model_def' AS rsrc
FROM {{ source('herd', 'model_def') }}
