-- Satellite: Skill descriptive attributes (historized)
-- materialized='incremental', unique_key='skill_tk || load_ts'

WITH source AS (
    SELECT
        {{ generate_hash('skillset_code') }} AS skill_tk,
        skillset_description AS skill_description,
        is_deleted,
        {{ hashdiff(['skillset_description', 'is_deleted']) }} AS skill_base_hd,
        load_ts,
        rsrc
    FROM {{ ref('stg_herd__skillset_def') }}
)

SELECT s.*
FROM source s
{% if is_incremental() %}
LEFT JOIN (
    SELECT skill_tk, skill_base_hd
    FROM {{ this }}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY skill_tk ORDER BY load_ts DESC) = 1
) AS existing
    ON s.skill_tk = existing.skill_tk
    AND s.skill_base_hd = existing.skill_base_hd
WHERE existing.skill_tk IS NULL
{% endif %}
