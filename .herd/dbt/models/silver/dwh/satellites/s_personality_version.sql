-- Satellite: Personality version history (historized - immutable)
-- materialized='incremental', unique_key='personality_tk || load_ts'

WITH source AS (
    SELECT
        {{ generate_hash('personality_code') }} AS personality_tk,
        personality_version_code,
        personality_version_content,
        {{ hashdiff(['personality_version_code', 'personality_version_content']) }} AS personality_version_hd,
        load_ts,
        rsrc
    FROM {{ ref('stg_herd__personality_version') }}
)

SELECT s.*
FROM source s
{% if is_incremental() %}
LEFT JOIN (
    SELECT personality_tk, personality_version_hd
    FROM {{ this }}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY personality_tk ORDER BY load_ts DESC) = 1
) AS existing
    ON s.personality_tk = existing.personality_tk
    AND s.personality_version_hd = existing.personality_version_hd
WHERE existing.personality_tk IS NULL
{% endif %}
