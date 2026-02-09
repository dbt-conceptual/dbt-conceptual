{% macro current_timestamp_utc() %}
    CURRENT_TIMESTAMP AT TIME ZONE 'UTC'
{% endmacro %}
