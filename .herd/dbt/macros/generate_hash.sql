{% macro generate_hash(columns) %}
    {% if columns is string %}
        SHA1(LOWER({{ columns }}))
    {% else %}
        SHA1(LOWER(CONCAT_WS('|', {{ columns | join(', ') }})))
    {% endif %}
{% endmacro %}
