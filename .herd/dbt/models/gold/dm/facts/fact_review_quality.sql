-- Fact: Review Quality
-- Grain: one row per review
-- Tracks review quality metrics and findings

WITH review_base AS (
    SELECT
        ln.review_submission_tk,
        ln.review_tk,
        ln.pull_request_tk,
        ln.agent_tk,
        ln.review_round,
        ln.review_verdict,
        ln.review_duration_minutes,
        ln.load_ts AS review_completed_at
    FROM {{ ref('ln_review_submission') }} ln
),

finding_aggregates AS (
    SELECT
        review_tk,
        COUNT(*) AS finding_count,
        SUM(CASE WHEN finding_severity = 'blocking' THEN 1 ELSE 0 END) AS blocking_finding_count,
        SUM(CASE WHEN finding_severity = 'advisory' THEN 1 ELSE 0 END) AS advisory_finding_count,
        COUNT(DISTINCT finding_pattern_id) AS unique_pattern_count,
        SUM(CASE WHEN finding_outcome = 'accepted' THEN 1 ELSE 0 END) AS accepted_finding_count,
        SUM(CASE WHEN finding_outcome = 'disputed' THEN 1 ELSE 0 END) AS disputed_finding_count,
        SUM(CASE WHEN finding_outcome = 'deferred' THEN 1 ELSE 0 END) AS deferred_finding_count
    FROM {{ ref('sn_review_finding') }}
    GROUP BY review_tk
)

SELECT
    rb.review_submission_tk,
    rb.review_tk,

    -- Type 1 join to dim_pull_request
    rb.pull_request_tk AS pull_request_sk,

    -- Type 2 SCD join to dim_agent using valid_from/valid_to
    da.agent_sk,

    rb.review_round,
    rb.review_verdict,
    rb.review_duration_minutes,
    rb.review_completed_at,

    -- Finding metrics
    COALESCE(fa.finding_count, 0) AS finding_count,
    COALESCE(fa.blocking_finding_count, 0) AS blocking_finding_count,
    COALESCE(fa.advisory_finding_count, 0) AS advisory_finding_count,
    COALESCE(fa.unique_pattern_count, 0) AS unique_pattern_count,
    COALESCE(fa.accepted_finding_count, 0) AS accepted_finding_count,
    COALESCE(fa.disputed_finding_count, 0) AS disputed_finding_count,
    COALESCE(fa.deferred_finding_count, 0) AS deferred_finding_count

FROM review_base rb

-- Type 2 SCD join: match agent at the time of review completion
LEFT JOIN {{ ref('dim_agent') }} da
    ON rb.agent_tk = da.agent_tk
    AND rb.review_completed_at >= da.valid_from
    AND rb.review_completed_at < da.valid_to

LEFT JOIN finding_aggregates fa
    ON rb.review_tk = fa.review_tk
