-- Hub: Skill business key (individual skill capability from skillset_def)
-- materialized='incremental', unique_key='skill_tk'

SELECT
    {{ generate_hash('skillset_code') }} AS skill_tk,
    skillset_code AS skill_code,
    load_ts,
    rsrc
FROM {{ ref('stg_herd__skillset_def') }}
{% if is_incremental() %}
WHERE {{ generate_hash('skillset_code') }} NOT IN (SELECT skill_tk FROM {{ this }})
{% endif %}
