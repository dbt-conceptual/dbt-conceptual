-- Dimension: Pull Request (Type 1)
-- Grain: one row per pull request (current state only)
-- TK aliased as SK

SELECT
    h.pull_request_tk AS pull_request_sk,
    h.pr_code,
    s.ticket_code,
    s.pr_branch_name,
    s.pr_title,
    s.pr_lines_added,
    s.pr_lines_deleted,
    s.pr_files_changed,
    s.pr_merged_at,
    s.pr_closed_at,
    s.is_deleted
FROM {{ ref('h_pull_request') }} h
JOIN {{ ref('s_pull_request_base') }} s
    ON h.pull_request_tk = s.pull_request_tk
QUALIFY ROW_NUMBER() OVER (PARTITION BY h.pull_request_tk ORDER BY s.load_ts DESC) = 1
