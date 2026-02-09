-- Dimension: Date (Generated)
-- Grain: one row per date
-- Date spine from 2025-01-01 to 2027-12-31

WITH date_spine AS (
    SELECT
        CAST(range AS DATE) AS date_actual
    FROM range(
        DATE '2025-01-01',
        DATE '2027-12-31' + INTERVAL 1 DAY,
        INTERVAL 1 DAY
    )
)

SELECT
    CAST(strftime(date_actual, '%Y%m%d') AS INTEGER) AS date_sk,
    date_actual,
    DAYOFWEEK(date_actual) AS day_of_week,
    DAYNAME(date_actual) AS day_name,
    MONTH(date_actual) AS month_number,
    MONTHNAME(date_actual) AS month_name,
    QUARTER(date_actual) AS quarter,
    YEAR(date_actual) AS year,
    CASE WHEN DAYOFWEEK(date_actual) IN (1, 7) THEN TRUE ELSE FALSE END AS is_weekend
FROM date_spine
