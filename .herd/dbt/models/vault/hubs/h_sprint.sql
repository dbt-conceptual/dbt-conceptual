-- Hub: Sprint business key
-- materialized='incremental', unique_key='sprint_tk'

SELECT
    {{ generate_hash('sprint_code') }} AS sprint_tk,
    sprint_code,
    load_ts,
    rsrc
FROM {{ ref('stg_herd__sprint_def') }}
{% if is_incremental() %}
WHERE {{ generate_hash('sprint_code') }} NOT IN (SELECT sprint_tk FROM {{ this }})
{% endif %}
