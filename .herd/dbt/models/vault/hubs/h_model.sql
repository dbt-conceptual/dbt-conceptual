-- Hub: Model business key
-- materialized='incremental', unique_key='model_tk'

SELECT
    {{ generate_hash('model_code') }} AS model_tk,
    model_code,
    load_ts,
    rsrc
FROM {{ ref('stg_herd__model_def') }}
{% if is_incremental() %}
WHERE {{ generate_hash('model_code') }} NOT IN (SELECT model_tk FROM {{ this }})
{% endif %}
