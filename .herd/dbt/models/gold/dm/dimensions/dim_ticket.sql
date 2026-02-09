-- Dimension: Ticket (Type 2 SCD)
-- Grain: one row per ticket per version
-- Tracks historical changes to ticket attributes

WITH ticket_history AS (
    SELECT
        h.ticket_tk,
        h.ticket_code,
        s.ticket_title,
        s.ticket_description,
        s.ticket_tshirt_size,
        s.ticket_acceptance_criteria,
        s.ticket_current_status,
        s.current_sprint_code,
        s.project_code,
        s.is_deleted,
        s.load_ts AS valid_from,
        LEAD(s.load_ts) OVER (PARTITION BY h.ticket_tk ORDER BY s.load_ts) AS valid_to
    FROM {{ ref('h_ticket') }} h
    JOIN {{ ref('s_ticket_base') }} s
        ON h.ticket_tk = s.ticket_tk
)

SELECT
    {{ generate_hash(['ticket_tk', 'valid_from']) }} AS ticket_sk,
    ticket_tk,
    ticket_code,
    ticket_title,
    ticket_description,
    ticket_tshirt_size,
    ticket_acceptance_criteria,
    ticket_current_status,
    current_sprint_code,
    project_code,
    is_deleted,
    valid_from,
    COALESCE(valid_to, CAST('9999-12-31' AS TIMESTAMP)) AS valid_to,
    CASE WHEN valid_to IS NULL THEN TRUE ELSE FALSE END AS is_current
FROM ticket_history
