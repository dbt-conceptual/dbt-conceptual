-- Hub: Ticket business key
-- materialized='incremental', unique_key='ticket_tk'

SELECT
    {{ generate_hash('ticket_code') }} AS ticket_tk,
    ticket_code,
    load_ts,
    rsrc
FROM {{ ref('stg_herd__ticket_def') }}
{% if is_incremental() %}
WHERE {{ generate_hash('ticket_code') }} NOT IN (SELECT ticket_tk FROM {{ this }})
{% endif %}
