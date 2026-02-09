-- Satellite: Agent descriptive attributes (historized)
-- materialized='incremental', unique_key='agent_tk || load_ts'

WITH source AS (
    SELECT
        {{ generate_hash('agent_code') }} AS agent_tk,
        agent_role,
        agent_status,
        agent_branch_prefix,
        agent_email,
        default_model_code,
        is_deleted,
        {{ hashdiff(['agent_role', 'agent_status', 'agent_branch_prefix', 'agent_email', 'default_model_code', 'is_deleted']) }} AS agent_base_hd,
        load_ts,
        rsrc
    FROM {{ ref('stg_herd__agent_def') }}
)

SELECT s.*
FROM source s
{% if is_incremental() %}
LEFT JOIN (
    SELECT agent_tk, agent_base_hd
    FROM {{ this }}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY agent_tk ORDER BY load_ts DESC) = 1
) AS existing
    ON s.agent_tk = existing.agent_tk
    AND s.agent_base_hd = existing.agent_base_hd
WHERE existing.agent_tk IS NULL
{% endif %}
