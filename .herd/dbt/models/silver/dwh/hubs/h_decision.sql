-- Hub: Decision business key
-- materialized='incremental', unique_key='decision_tk'

SELECT
    {{ generate_hash('decision_id') }} AS decision_tk,
    decision_id,
    load_ts,
    rsrc
FROM {{ ref('stg_herd__decision_record') }}
{% if is_incremental() %}
WHERE {{ generate_hash('decision_id') }} NOT IN (SELECT decision_tk FROM {{ this }})
{% endif %}
