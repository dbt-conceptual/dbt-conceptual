-- Non-historized Satellite: Review findings (append-only)
-- materialized='incremental', no hashdiff, no dedup

SELECT
    {{ generate_hash('review_code') }} AS review_tk,
    review_finding_code,
    finding_category,
    finding_severity,
    finding_description,
    finding_file_path,
    finding_line_number,
    finding_pattern_id,
    finding_outcome,
    load_ts,
    rsrc
FROM {{ ref('stg_herd__review_finding') }}
{% if is_incremental() %}
WHERE load_ts > (SELECT COALESCE(MAX(load_ts), '1900-01-01') FROM {{ this }})
{% endif %}
