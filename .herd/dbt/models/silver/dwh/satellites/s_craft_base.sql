-- Satellite: Craft descriptive attributes (historized)
-- materialized='incremental', unique_key='craft_tk || load_ts'

WITH source AS (
    SELECT
        {{ generate_hash('craft_code') }} AS craft_tk,
        craft_description,
        is_deleted,
        {{ hashdiff(['craft_description', 'is_deleted']) }} AS craft_base_hd,
        load_ts,
        rsrc
    FROM {{ ref('stg_herd__craft_def') }}
)

SELECT s.*
FROM source s
{% if is_incremental() %}
LEFT JOIN (
    SELECT craft_tk, craft_base_hd
    FROM {{ this }}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY craft_tk ORDER BY load_ts DESC) = 1
) AS existing
    ON s.craft_tk = existing.craft_tk
    AND s.craft_base_hd = existing.craft_base_hd
WHERE existing.craft_tk IS NULL
{% endif %}
