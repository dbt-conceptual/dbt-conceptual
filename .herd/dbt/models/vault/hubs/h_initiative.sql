-- Hub: Initiative business key
-- materialized='incremental', unique_key='initiative_tk'

SELECT
    {{ generate_hash('initiative_code') }} AS initiative_tk,
    initiative_code,
    load_ts,
    rsrc
FROM {{ ref('stg_herd__initiative_def') }}
{% if is_incremental() %}
WHERE {{ generate_hash('initiative_code') }} NOT IN (SELECT initiative_tk FROM {{ this }})
{% endif %}
