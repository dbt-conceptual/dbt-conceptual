-- Satellite: Review descriptive attributes (historized - immutable, no is_deleted)
-- materialized='incremental', unique_key='review_tk || load_ts'

WITH source AS (
    SELECT
        {{ generate_hash('review_code') }} AS review_tk,
        review_round,
        review_verdict,
        review_duration_minutes,
        {{ hashdiff(['review_round', 'review_verdict', 'review_duration_minutes']) }} AS review_base_hd,
        load_ts,
        rsrc
    FROM {{ ref('stg_herd__review_def') }}
)

SELECT s.*
FROM source s
{% if is_incremental() %}
LEFT JOIN (
    SELECT review_tk, review_base_hd
    FROM {{ this }}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY review_tk ORDER BY load_ts DESC) = 1
) AS existing
    ON s.review_tk = existing.review_tk
    AND s.review_base_hd = existing.review_base_hd
WHERE existing.review_tk IS NULL
{% endif %}
