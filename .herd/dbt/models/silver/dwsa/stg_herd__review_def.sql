-- Review definitions staging model (immutable)
SELECT
    review_code,
    pr_code,
    reviewer_agent_instance_code,
    review_round,
    review_verdict,
    review_duration_minutes,
    FALSE AS is_deleted,
    created_at AS load_ts,
    'herd.review_def' AS rsrc
FROM {{ source('herd', 'review_def') }}
