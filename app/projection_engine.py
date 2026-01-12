"""
Actuarial projection engine for term life insurance.

Runs month-by-month projections calculating:
- Deaths (using mortality tables)
- Premiums collected
- Claims paid
- Reserves (simple prospective reserve)
"""

import pandas as pd
from typing import List
from .models import Assumptions, ProjectionRow, ProjectionResult, ProjectionSummary
from .mortality_tables import get_qx, annual_to_monthly_qx


def calculate_reserve(
    policies: float,
    sum_assured: float,
    monthly_premium: float,
    entry_age: int,
    current_month: int,
    term_months: int,
    annual_interest_rate: float,
    mortality_table: str = "ELT17_MALES"
) -> float:
    """
    Calculate the prospective reserve at a given point.

    Reserve = PV(future benefits) - PV(future premiums)

    This is a simplified calculation assuming:
    - Deaths occur at the start of each month
    - Premiums are paid at the start of each month
    - Interest is earned monthly
    """
    if current_month >= term_months:
        return 0.0

    monthly_rate = (1 + annual_interest_rate) ** (1/12) - 1
    remaining_months = term_months - current_month

    pv_benefits = 0.0
    pv_premiums = 0.0

    # Start with current number of policies
    expected_policies = policies

    for t in range(remaining_months):
        future_month = current_month + t
        age_at_t = entry_age + (future_month // 12)
        qx_annual = get_qx(age_at_t, mortality_table)
        qx_monthly = annual_to_monthly_qx(qx_annual)

        # Discount factor
        discount = (1 + monthly_rate) ** (-t)

        # Expected deaths this month
        expected_deaths = expected_policies * qx_monthly

        # PV of death benefits
        pv_benefits += expected_deaths * sum_assured * discount

        # PV of premiums (paid by survivors at start of month)
        pv_premiums += expected_policies * monthly_premium * discount

        # Survivors continue to next month
        expected_policies -= expected_deaths

    reserve = pv_benefits - pv_premiums
    return max(0, reserve)  # Reserve cannot be negative for a single policy


def run_projection(assumptions: Assumptions) -> ProjectionResult:
    """
    Run a month-by-month actuarial projection.

    Args:
        assumptions: The structured assumptions for the projection

    Returns:
        ProjectionResult containing all monthly rows and summary statistics
    """
    term_months = assumptions.term_years * 12
    rows: List[ProjectionRow] = []

    # Track running totals
    policies_in_force = float(assumptions.num_policies)
    total_premiums = 0.0
    total_claims = 0.0
    total_deaths = 0.0
    peak_reserve = 0.0

    for month in range(1, term_months + 1):
        # Calculate policy year (1-indexed)
        policy_year = ((month - 1) // 12) + 1

        # Calculate attained age at start of month
        age = assumptions.entry_age + ((month - 1) // 12)

        # Get mortality rate
        qx_annual = get_qx(age, assumptions.mortality_table)
        qx_monthly = annual_to_monthly_qx(qx_annual)

        # Calculate expected deaths
        deaths = policies_in_force * qx_monthly

        # Calculate premiums (from survivors at start of month)
        premiums = policies_in_force * assumptions.monthly_premium

        # Calculate claims
        claims = deaths * assumptions.sum_assured

        # Update policies in force
        policies_at_start = policies_in_force
        policies_in_force -= deaths

        # Calculate reserve at end of month
        reserve = calculate_reserve(
            policies=policies_in_force,
            sum_assured=assumptions.sum_assured,
            monthly_premium=assumptions.monthly_premium,
            entry_age=assumptions.entry_age,
            current_month=month,
            term_months=term_months,
            annual_interest_rate=assumptions.interest_rate,
            mortality_table=assumptions.mortality_table
        )

        # Update totals
        total_premiums += premiums
        total_claims += claims
        total_deaths += deaths
        peak_reserve = max(peak_reserve, reserve)

        # Create row
        row = ProjectionRow(
            month=month,
            year=policy_year,
            age=age,
            policies_start=round(policies_at_start, 4),
            deaths=round(deaths, 4),
            policies_end=round(policies_in_force, 4),
            premiums=round(premiums, 2),
            claims=round(claims, 2),
            net_cashflow=round(premiums - claims, 2),
            reserve=round(reserve, 2)
        )
        rows.append(row)

    # Create summary
    summary = ProjectionSummary(
        total_months=term_months,
        total_premiums=round(total_premiums, 2),
        total_claims=round(total_claims, 2),
        total_deaths=round(total_deaths, 4),
        final_in_force=round(policies_in_force, 4),
        peak_reserve=round(peak_reserve, 2)
    )

    return ProjectionResult(
        assumptions=assumptions,
        rows=rows,
        summary=summary
    )


def projection_to_dataframe(result: ProjectionResult) -> pd.DataFrame:
    """Convert projection result to a pandas DataFrame."""
    data = [row.model_dump() for row in result.rows]
    df = pd.DataFrame(data)
    return df


def projection_to_csv(result: ProjectionResult) -> str:
    """Convert projection result to CSV string."""
    df = projection_to_dataframe(result)
    return df.to_csv(index=False)
