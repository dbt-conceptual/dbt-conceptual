-- Satellite: Observation descriptive attributes (historized)
-- materialized='incremental', unique_key='observation_tk || load_ts'

WITH source AS (
    SELECT
        {{ generate_hash('observation_id') }} AS observation_tk,
        agent_code,
        session_code,
        observation_type,
        observation_content,
        confidence,
        is_deleted,
        {{ hashdiff(['agent_code', 'session_code', 'observation_type', 'observation_content', 'confidence', 'is_deleted']) }} AS observation_base_hd,
        load_ts,
        rsrc
    FROM {{ ref('stg_herd__agent_observation') }}
)

SELECT s.*
FROM source s
{% if is_incremental() %}
LEFT JOIN (
    SELECT observation_tk, observation_base_hd
    FROM {{ this }}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY observation_tk ORDER BY load_ts DESC) = 1
) AS existing
    ON s.observation_tk = existing.observation_tk
    AND s.observation_base_hd = existing.observation_base_hd
WHERE existing.observation_tk IS NULL
{% endif %}
