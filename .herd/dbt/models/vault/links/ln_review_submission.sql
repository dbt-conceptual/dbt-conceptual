-- Transactional Link: Review of a PR
-- materialized='incremental', unique_key='review_submission_tk'

SELECT
    SHA1(LOWER(CONCAT_WS('|', r.review_code, r.pr_code))) AS review_submission_tk,
    {{ generate_hash('r.review_code') }} AS review_tk,
    {{ generate_hash('r.pr_code') }} AS pull_request_tk,
    {{ generate_hash('ai.agent_code') }} AS agent_tk,
    r.reviewer_agent_instance_code,
    r.review_round,
    r.review_verdict,
    r.review_duration_minutes,
    r.load_ts,
    r.rsrc
FROM {{ ref('stg_herd__review_def') }} r
JOIN {{ ref('stg_herd__agent_instance') }} ai ON r.reviewer_agent_instance_code = ai.agent_instance_code
{% if is_incremental() %}
WHERE SHA1(LOWER(CONCAT_WS('|', r.review_code, r.pr_code))) NOT IN (SELECT review_submission_tk FROM {{ this }})
{% endif %}
