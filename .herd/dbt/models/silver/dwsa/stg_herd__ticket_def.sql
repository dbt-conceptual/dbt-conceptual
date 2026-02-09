-- Ticket definitions staging model
SELECT
    ticket_code,
    project_code,
    ticket_title,
    ticket_description,
    ticket_tshirt_size,
    ticket_acceptance_criteria,
    ticket_current_status,
    current_sprint_code,
    CASE WHEN deleted_at IS NOT NULL THEN TRUE ELSE FALSE END AS is_deleted,
    COALESCE(modified_at, created_at) AS load_ts,
    'herd.ticket_def' AS rsrc
FROM {{ source('herd', 'ticket_def') }}
