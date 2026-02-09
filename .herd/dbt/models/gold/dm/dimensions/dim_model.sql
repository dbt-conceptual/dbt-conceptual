-- Dimension: Model (Type 1)
-- Grain: one row per model (current state only)
-- TK aliased as SK

SELECT
    h.model_tk AS model_sk,
    h.model_code,
    s.model_provider,
    s.model_context_window,
    s.model_input_cost_per_m,
    s.model_output_cost_per_m,
    s.model_cache_read_cost_per_m,
    s.model_cache_create_cost_per_m,
    s.is_deleted
FROM {{ ref('h_model') }} h
JOIN {{ ref('s_model_base') }} s
    ON h.model_tk = s.model_tk
QUALIFY ROW_NUMBER() OVER (PARTITION BY h.model_tk ORDER BY s.load_ts DESC) = 1
