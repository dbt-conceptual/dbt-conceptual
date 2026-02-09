-- Satellite: Personality descriptive attributes (historized)
-- materialized='incremental', unique_key='personality_tk || load_ts'

WITH source AS (
    SELECT
        {{ generate_hash('personality_code') }} AS personality_tk,
        personality_description,
        is_deleted,
        {{ hashdiff(['personality_description', 'is_deleted']) }} AS personality_base_hd,
        load_ts,
        rsrc
    FROM {{ ref('stg_herd__personality_def') }}
)

SELECT s.*
FROM source s
{% if is_incremental() %}
LEFT JOIN (
    SELECT personality_tk, personality_base_hd
    FROM {{ this }}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY personality_tk ORDER BY load_ts DESC) = 1
) AS existing
    ON s.personality_tk = existing.personality_tk
    AND s.personality_base_hd = existing.personality_base_hd
WHERE existing.personality_tk IS NULL
{% endif %}
