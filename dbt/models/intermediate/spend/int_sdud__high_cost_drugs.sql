WITH staging AS (
    SELECT *
    FROM {{ ref('stg_sdud') }}
),

aggregate_reimbursements AS (
    SELECT *,
        SUM(medicaid_amount_reimbursed) OVER(PARTITION BY calendar_year) AS total_annual_reimbursed
        SUM(medicaid_amount_reimbursed) OVER(PARTITION BY calendar_year, ndc) AS reimbursed_per_drug
    FROM staging 
),

calculations AS (
    SELECT *,
        reimbursed_per_drug - (0.005 * total_annual_reimbursed) AS excess_amount
        CASE
            WHEN excess_amount > 0 THEN TRUE
            ELSE FALSE
        END AS is_high_cost_drug
    FROM aggregate_reimbursements
)

SELECT
    sdud_id,
    calendar_year,
    ndc,
    product_name,
    reimbursed_per_drug,
    is_high_cost_drug,
    excess_amount
FROM calculations 
ORDER BY reimbursed_per_drug DESC
