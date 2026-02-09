-- Hub: Agent business key
-- materialized='incremental', unique_key='agent_tk'

SELECT
    {{ generate_hash('agent_code') }} AS agent_tk,
    agent_code,
    load_ts,
    rsrc
FROM {{ ref('stg_herd__agent_def') }}
{% if is_incremental() %}
WHERE {{ generate_hash('agent_code') }} NOT IN (SELECT agent_tk FROM {{ this }})
{% endif %}
