-- Hub: Project business key
-- materialized='incremental', unique_key='project_tk'

SELECT
    {{ generate_hash('project_code') }} AS project_tk,
    project_code,
    load_ts,
    rsrc
FROM {{ ref('stg_herd__project_def') }}
{% if is_incremental() %}
WHERE {{ generate_hash('project_code') }} NOT IN (SELECT project_tk FROM {{ this }})
{% endif %}
