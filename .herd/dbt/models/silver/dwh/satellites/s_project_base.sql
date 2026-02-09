-- Satellite: Project descriptive attributes (historized)
-- materialized='incremental', unique_key='project_tk || load_ts'

WITH source AS (
    SELECT
        {{ generate_hash('project_code') }} AS project_tk,
        project_title,
        project_description,
        project_status,
        is_deleted,
        {{ hashdiff(['project_title', 'project_description', 'project_status', 'is_deleted']) }} AS project_base_hd,
        load_ts,
        rsrc
    FROM {{ ref('stg_herd__project_def') }}
)

SELECT s.*
FROM source s
{% if is_incremental() %}
LEFT JOIN (
    SELECT project_tk, project_base_hd
    FROM {{ this }}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY project_tk ORDER BY load_ts DESC) = 1
) AS existing
    ON s.project_tk = existing.project_tk
    AND s.project_base_hd = existing.project_base_hd
WHERE existing.project_tk IS NULL
{% endif %}
