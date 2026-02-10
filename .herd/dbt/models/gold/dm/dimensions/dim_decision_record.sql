-- Dimension: Decision Record
-- Type 2 SCD with valid_from/valid_to
-- Tracks architectural and operational decision records

WITH decision_history AS (
    SELECT
        dec.decision_tk,
        dec.decision_id,
        sat.decision_type,
        sat.context,
        sat.decision,
        sat.rationale,
        sat.alternatives_considered,
        sat.decided_by,
        sat.ticket_code,
        sat.is_deleted,
        sat.load_ts AS valid_from,
        LEAD(sat.load_ts) OVER (PARTITION BY dec.decision_tk ORDER BY sat.load_ts) AS valid_to
    FROM {{ ref('h_decision') }} dec
    INNER JOIN {{ ref('s_decision_base') }} sat
        ON dec.decision_tk = sat.decision_tk
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['decision_tk', 'valid_from']) }} AS decision_sk,
    decision_tk,
    decision_id,
    decision_type,
    context,
    decision,
    rationale,
    alternatives_considered,
    decided_by,
    ticket_code,
    is_deleted,
    valid_from,
    COALESCE(valid_to, '9999-12-31'::TIMESTAMP) AS valid_to,
    CASE WHEN valid_to IS NULL THEN TRUE ELSE FALSE END AS is_current
FROM decision_history
