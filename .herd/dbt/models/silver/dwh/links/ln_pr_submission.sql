-- Transactional Link: PR created for a ticket
-- materialized='incremental', unique_key='pr_submission_tk'

SELECT
    SHA1(LOWER(CONCAT_WS('|', p.pr_code, p.ticket_code))) AS pr_submission_tk,
    {{ generate_hash('p.pr_code') }} AS pull_request_tk,
    {{ generate_hash('p.ticket_code') }} AS ticket_tk,
    {{ generate_hash('ai.agent_code') }} AS agent_tk,
    p.creator_agent_instance_code,
    p.pr_branch_name,
    p.pr_lines_added,
    p.pr_lines_deleted,
    p.pr_files_changed,
    p.load_ts,
    p.rsrc
FROM {{ ref('stg_herd__pr_def') }} p
JOIN {{ ref('stg_herd__agent_instance') }} ai ON p.creator_agent_instance_code = ai.agent_instance_code
{% if is_incremental() %}
WHERE SHA1(LOWER(CONCAT_WS('|', p.pr_code, p.ticket_code))) NOT IN (SELECT pr_submission_tk FROM {{ this }})
{% endif %}
