{% macro hashdiff(columns) %}
    SHA1(LOWER(CONCAT_WS('|',
        {% for col in columns %}
            CAST({{ col }} AS TEXT){% if not loop.last %}, {% endif %}
        {% endfor %}
    )))
{% endmacro %}
