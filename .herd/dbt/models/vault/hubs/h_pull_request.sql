-- Hub: Pull Request business key
-- materialized='incremental', unique_key='pull_request_tk'

SELECT
    {{ generate_hash('pr_code') }} AS pull_request_tk,
    pr_code,
    load_ts,
    rsrc
FROM {{ ref('stg_herd__pr_def') }}
{% if is_incremental() %}
WHERE {{ generate_hash('pr_code') }} NOT IN (SELECT pull_request_tk FROM {{ this }})
{% endif %}
