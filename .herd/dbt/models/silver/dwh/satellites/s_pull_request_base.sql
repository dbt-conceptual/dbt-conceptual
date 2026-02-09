-- Satellite: Pull Request descriptive attributes (historized)
-- materialized='incremental', unique_key='pull_request_tk || load_ts'

WITH source AS (
    SELECT
        {{ generate_hash('pr_code') }} AS pull_request_tk,
        pr_branch_name,
        pr_title,
        pr_lines_added,
        pr_lines_deleted,
        pr_files_changed,
        pr_merged_at,
        pr_closed_at,
        is_deleted,
        {{ hashdiff(['pr_branch_name', 'pr_title', 'pr_lines_added', 'pr_lines_deleted', 'pr_files_changed', 'pr_merged_at', 'pr_closed_at', 'is_deleted']) }} AS pull_request_base_hd,
        load_ts,
        rsrc
    FROM {{ ref('stg_herd__pr_def') }}
)

SELECT s.*
FROM source s
{% if is_incremental() %}
LEFT JOIN (
    SELECT pull_request_tk, pull_request_base_hd
    FROM {{ this }}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY pull_request_tk ORDER BY load_ts DESC) = 1
) AS existing
    ON s.pull_request_tk = existing.pull_request_tk
    AND s.pull_request_base_hd = existing.pull_request_base_hd
WHERE existing.pull_request_tk IS NULL
{% endif %}
