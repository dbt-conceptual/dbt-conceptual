-- Satellite: Ticket descriptive attributes (historized)
-- materialized='incremental', unique_key='ticket_tk || load_ts'

WITH source AS (
    SELECT
        {{ generate_hash('ticket_code') }} AS ticket_tk,
        ticket_title,
        ticket_description,
        ticket_tshirt_size,
        ticket_acceptance_criteria,
        ticket_current_status,
        project_code,
        current_sprint_code,
        is_deleted,
        {{ hashdiff(['ticket_title', 'ticket_description', 'ticket_tshirt_size', 'ticket_acceptance_criteria', 'ticket_current_status', 'project_code', 'current_sprint_code', 'is_deleted']) }} AS ticket_base_hd,
        load_ts,
        rsrc
    FROM {{ ref('stg_herd__ticket_def') }}
)

SELECT s.*
FROM source s
{% if is_incremental() %}
LEFT JOIN (
    SELECT ticket_tk, ticket_base_hd
    FROM {{ this }}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY ticket_tk ORDER BY load_ts DESC) = 1
) AS existing
    ON s.ticket_tk = existing.ticket_tk
    AND s.ticket_base_hd = existing.ticket_base_hd
WHERE existing.ticket_tk IS NULL
{% endif %}
