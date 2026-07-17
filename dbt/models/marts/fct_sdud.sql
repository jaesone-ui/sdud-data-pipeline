WITH sdud AS (
    SELECT *
    FROM {{ ref('stg_sdud') }}
)

SELECT
    to_hex(md5(concat(
        coalesce(us_state, '_null_'), '-',
        coalesce(cast(calendar_year AS string), '_null_'), '-',
        coalesce(cast(calendar_quarter AS string), '_null_'), '-',
        coalesce(ndc, '_null_')
    ))) AS sdud_id,
    calendar_year,
    calendar_quarter,
    us_state,
    ndc,
    medicaid_amount_reimbursed,
    number_of_prescriptions,
    units_reimbursed
FROM sdud