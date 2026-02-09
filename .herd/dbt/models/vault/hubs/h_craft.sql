-- Hub: Craft business key
-- materialized='incremental', unique_key='craft_tk'

SELECT
    {{ generate_hash('craft_code') }} AS craft_tk,
    craft_code,
    load_ts,
    rsrc
FROM {{ ref('stg_herd__craft_def') }}
{% if is_incremental() %}
WHERE {{ generate_hash('craft_code') }} NOT IN (SELECT craft_tk FROM {{ this }})
{% endif %}
