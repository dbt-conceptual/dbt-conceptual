-- Satellite: Craft version history (historized - immutable, every row is new version)
-- materialized='incremental', unique_key='craft_tk || load_ts'

WITH source AS (
    SELECT
        {{ generate_hash('craft_code') }} AS craft_tk,
        craft_version_code,
        craft_version_content,
        {{ hashdiff(['craft_version_code', 'craft_version_content']) }} AS craft_version_hd,
        load_ts,
        rsrc
    FROM {{ ref('stg_herd__craft_version') }}
)

SELECT s.*
FROM source s
{% if is_incremental() %}
LEFT JOIN (
    SELECT craft_tk, craft_version_hd
    FROM {{ this }}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY craft_tk ORDER BY load_ts DESC) = 1
) AS existing
    ON s.craft_tk = existing.craft_tk
    AND s.craft_version_hd = existing.craft_version_hd
WHERE existing.craft_tk IS NULL
{% endif %}
