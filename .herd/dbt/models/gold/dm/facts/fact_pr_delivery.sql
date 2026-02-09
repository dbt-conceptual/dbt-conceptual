-- Fact: PR Delivery
-- Grain: one row per pull request
-- Tracks PR delivery metrics and timing

WITH pr_base AS (
    SELECT
        ln.pr_submission_tk,
        ln.pull_request_tk,
        ln.ticket_tk,
        ln.agent_tk,
        ln.pr_lines_added,
        ln.pr_lines_deleted,
        ln.pr_files_changed,
        ln.load_ts AS pr_created_at,
        s.pr_merged_at,
        s.pr_closed_at
    FROM {{ ref('ln_pr_submission') }} ln
    JOIN {{ ref('s_pull_request_base') }} s
        ON ln.pull_request_tk = s.pull_request_tk
    QUALIFY ROW_NUMBER() OVER (PARTITION BY ln.pull_request_tk ORDER BY s.load_ts DESC) = 1
),

review_counts AS (
    SELECT
        pull_request_tk,
        COUNT(*) AS review_count
    FROM {{ ref('ln_review_submission') }}
    GROUP BY pull_request_tk
)

SELECT
    pb.pr_submission_tk,

    -- Type 1 join to dim_pull_request
    pb.pull_request_tk AS pull_request_sk,

    -- Type 2 SCD join to dim_ticket using valid_from/valid_to
    dt.ticket_sk,

    -- Type 2 SCD join to dim_agent using valid_from/valid_to
    da.agent_sk,

    pb.pr_created_at,
    pb.pr_merged_at,
    pb.pr_closed_at,

    -- Delivery metrics
    pb.pr_lines_added,
    pb.pr_lines_deleted,
    pb.pr_files_changed,

    -- Derived measures
    CASE
        WHEN pb.pr_merged_at IS NOT NULL
        THEN EXTRACT(EPOCH FROM (pb.pr_merged_at - pb.pr_created_at)) / 60.0
        ELSE NULL
    END AS time_to_merge_minutes,

    COALESCE(rc.review_count, 0) AS review_count

FROM pr_base pb

-- Type 2 SCD join: match ticket at the time of PR creation
LEFT JOIN {{ ref('dim_ticket') }} dt
    ON pb.ticket_tk = dt.ticket_tk
    AND pb.pr_created_at >= dt.valid_from
    AND pb.pr_created_at < dt.valid_to

-- Type 2 SCD join: match agent at the time of PR creation
LEFT JOIN {{ ref('dim_agent') }} da
    ON pb.agent_tk = da.agent_tk
    AND pb.pr_created_at >= da.valid_from
    AND pb.pr_created_at < da.valid_to

LEFT JOIN review_counts rc
    ON pb.pull_request_tk = rc.pull_request_tk
