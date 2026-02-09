-- Hub: Personality business key
-- materialized='incremental', unique_key='personality_tk'

SELECT
    {{ generate_hash('personality_code') }} AS personality_tk,
    personality_code,
    load_ts,
    rsrc
FROM {{ ref('stg_herd__personality_def') }}
{% if is_incremental() %}
WHERE {{ generate_hash('personality_code') }} NOT IN (SELECT personality_tk FROM {{ this }})
{% endif %}
