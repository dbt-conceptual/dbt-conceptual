-- Satellite: Model descriptive attributes (historized)
-- materialized='incremental', unique_key='model_tk || load_ts'

WITH source AS (
    SELECT
        {{ generate_hash('model_code') }} AS model_tk,
        model_provider,
        model_context_window,
        model_input_cost_per_m,
        model_output_cost_per_m,
        model_cache_read_cost_per_m,
        model_cache_create_cost_per_m,
        is_deleted,
        {{ hashdiff(['model_provider', 'model_context_window', 'model_input_cost_per_m', 'model_output_cost_per_m', 'model_cache_read_cost_per_m', 'model_cache_create_cost_per_m', 'is_deleted']) }} AS model_base_hd,
        load_ts,
        rsrc
    FROM {{ ref('stg_herd__model_def') }}
)

SELECT s.*
FROM source s
{% if is_incremental() %}
LEFT JOIN (
    SELECT model_tk, model_base_hd
    FROM {{ this }}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY model_tk ORDER BY load_ts DESC) = 1
) AS existing
    ON s.model_tk = existing.model_tk
    AND s.model_base_hd = existing.model_base_hd
WHERE existing.model_tk IS NULL
{% endif %}
