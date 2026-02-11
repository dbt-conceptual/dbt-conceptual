-- Review findings staging model (immutable)
SELECT
    review_finding_code,
    review_code,
    finding_category,
    finding_severity,
    finding_description,
    finding_file_path,
    finding_line_number,
    finding_pattern_id,
    finding_outcome,
    FALSE AS is_deleted,
    created_at AS load_ts,
    'herd.review_finding' AS rsrc
FROM {{ source('herd', 'review_finding') }}
