-- Hub: Observation business key
-- materialized='incremental', unique_key='observation_tk'

SELECT
    {{ generate_hash('observation_id') }} AS observation_tk,
    observation_id,
    load_ts,
    rsrc
FROM {{ ref('stg_herd__agent_observation') }}
{% if is_incremental() %}
WHERE {{ generate_hash('observation_id') }} NOT IN (SELECT observation_tk FROM {{ this }})
{% endif %}
