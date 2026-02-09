-- Satellite: Skill version history (historized - immutable)
-- materialized='incremental', unique_key='skill_tk || load_ts'

WITH source AS (
    SELECT
        {{ generate_hash('skillset_code') }} AS skill_tk,
        skillset_version_code AS skill_version_code,
        skillset_version_content AS skill_version_content,
        {{ hashdiff(['skillset_version_code', 'skillset_version_content']) }} AS skill_version_hd,
        load_ts,
        rsrc
    FROM {{ ref('stg_herd__skillset_version') }}
)

SELECT s.*
FROM source s
{% if is_incremental() %}
LEFT JOIN (
    SELECT skill_tk, skill_version_hd
    FROM {{ this }}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY skill_tk ORDER BY load_ts DESC) = 1
) AS existing
    ON s.skill_tk = existing.skill_tk
    AND s.skill_version_hd = existing.skill_version_hd
WHERE existing.skill_tk IS NULL
{% endif %}
