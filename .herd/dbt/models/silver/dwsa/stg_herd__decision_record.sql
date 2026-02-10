-- Decision record staging model
SELECT
    decision_id,
    decision_type,
    context,
    decision,
    rationale,
    alternatives_considered,
    decided_by,
    ticket_code,
    deleted_at IS NOT NULL AS is_deleted,
    created_at AS load_ts,
    'herd.decision_record' AS rsrc
FROM {{ source('herd', 'decision_record') }}
