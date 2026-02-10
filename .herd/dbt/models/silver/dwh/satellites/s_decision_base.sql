-- Satellite: Decision descriptive attributes (historized)
-- materialized='incremental', unique_key='decision_tk || load_ts'

WITH source AS (
    SELECT
        {{ generate_hash('decision_id') }} AS decision_tk,
        decision_type,
        context,
        decision,
        rationale,
        alternatives_considered,
        decided_by,
        ticket_code,
        is_deleted,
        {{ hashdiff(['decision_type', 'context', 'decision', 'rationale', 'alternatives_considered', 'decided_by', 'ticket_code', 'is_deleted']) }} AS decision_base_hd,
        load_ts,
        rsrc
    FROM {{ ref('stg_herd__decision_record') }}
)

SELECT s.*
FROM source s
{% if is_incremental() %}
LEFT JOIN (
    SELECT decision_tk, decision_base_hd
    FROM {{ this }}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY decision_tk ORDER BY load_ts DESC) = 1
) AS existing
    ON s.decision_tk = existing.decision_tk
    AND s.decision_base_hd = existing.decision_base_hd
WHERE existing.decision_tk IS NULL
{% endif %}
