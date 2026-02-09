-- Satellite: Initiative descriptive attributes (historized)
-- materialized='incremental', unique_key='initiative_tk || load_ts'

WITH source AS (
    SELECT
        {{ generate_hash('initiative_code') }} AS initiative_tk,
        initiative_title,
        initiative_description,
        initiative_status,
        is_deleted,
        {{ hashdiff(['initiative_title', 'initiative_description', 'initiative_status', 'is_deleted']) }} AS initiative_base_hd,
        load_ts,
        rsrc
    FROM {{ ref('stg_herd__initiative_def') }}
)

SELECT s.*
FROM source s
{% if is_incremental() %}
LEFT JOIN (
    SELECT initiative_tk, initiative_base_hd
    FROM {{ this }}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY initiative_tk ORDER BY load_ts DESC) = 1
) AS existing
    ON s.initiative_tk = existing.initiative_tk
    AND s.initiative_base_hd = existing.initiative_base_hd
WHERE existing.initiative_tk IS NULL
{% endif %}
