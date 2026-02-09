-- Satellite: Sprint descriptive attributes (historized)
-- materialized='incremental', unique_key='sprint_tk || load_ts'

WITH source AS (
    SELECT
        {{ generate_hash('sprint_code') }} AS sprint_tk,
        sprint_title,
        sprint_goal,
        sprint_started_at,
        sprint_planned_end_at,
        sprint_actual_end_at,
        is_deleted,
        {{ hashdiff(['sprint_title', 'sprint_goal', 'sprint_started_at', 'sprint_planned_end_at', 'sprint_actual_end_at', 'is_deleted']) }} AS sprint_base_hd,
        load_ts,
        rsrc
    FROM {{ ref('stg_herd__sprint_def') }}
)

SELECT s.*
FROM source s
{% if is_incremental() %}
LEFT JOIN (
    SELECT sprint_tk, sprint_base_hd
    FROM {{ this }}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY sprint_tk ORDER BY load_ts DESC) = 1
) AS existing
    ON s.sprint_tk = existing.sprint_tk
    AND s.sprint_base_hd = existing.sprint_base_hd
WHERE existing.sprint_tk IS NULL
{% endif %}
