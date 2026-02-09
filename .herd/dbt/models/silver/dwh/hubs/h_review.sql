-- Hub: Review business key
-- materialized='incremental', unique_key='review_tk'

SELECT
    {{ generate_hash('review_code') }} AS review_tk,
    review_code,
    load_ts,
    rsrc
FROM {{ ref('stg_herd__review_def') }}
{% if is_incremental() %}
WHERE {{ generate_hash('review_code') }} NOT IN (SELECT review_tk FROM {{ this }})
{% endif %}
