"""Pydantic models for actuarial assumptions and projection results."""

from pydantic import BaseModel, Field
from typing import Optional


class Assumptions(BaseModel):
    """Structured actuarial assumptions parsed from natural language."""

    num_policies: int = Field(
        ...,
        gt=0,
        description="Number of policies in force at start"
    )
    sum_assured: float = Field(
        ...,
        gt=0,
        description="Sum assured per policy in GBP"
    )
    term_years: int = Field(
        ...,
        gt=0,
        le=50,
        description="Policy term in years"
    )
    entry_age: int = Field(
        ...,
        ge=18,
        le=80,
        description="Age at entry in complete years"
    )
    interest_rate: float = Field(
        ...,
        ge=0,
        le=1,
        description="Annual interest rate as decimal (e.g., 0.03 for 3%)"
    )
    monthly_premium: float = Field(
        ...,
        ge=0,
        description="Monthly premium per policy in GBP"
    )
    mortality_table: str = Field(
        default="ELT17_MALES",
        description="Mortality table to use"
    )


class ProjectionRow(BaseModel):
    """A single row in the cashflow projection."""

    month: int = Field(..., description="Month number (1, 2, 3, ...)")
    year: int = Field(..., description="Policy year (1, 2, 3, ...)")
    age: int = Field(..., description="Attained age at start of month")
    policies_start: float = Field(..., description="Policies in force at start of month")
    deaths: float = Field(..., description="Expected deaths during month")
    policies_end: float = Field(..., description="Policies in force at end of month")
    premiums: float = Field(..., description="Total premiums collected (GBP)")
    claims: float = Field(..., description="Total claims paid (GBP)")
    net_cashflow: float = Field(..., description="Net cashflow: premiums - claims (GBP)")
    reserve: float = Field(..., description="Reserve at end of month (GBP)")


class ProjectionResult(BaseModel):
    """Complete projection result."""

    assumptions: Assumptions
    rows: list[ProjectionRow]
    summary: "ProjectionSummary"


class ProjectionSummary(BaseModel):
    """Summary statistics for the projection."""

    total_months: int
    total_premiums: float
    total_claims: float
    total_deaths: float
    final_in_force: float
    peak_reserve: float


class ParseRequest(BaseModel):
    """Request to parse natural language input."""

    text: str = Field(..., min_length=10, description="Natural language description of assumptions")


class ParseResponse(BaseModel):
    """Response from parsing natural language."""

    success: bool
    assumptions: Optional[Assumptions] = None
    error: Optional[str] = None
    raw_input: str


class ProjectRequest(BaseModel):
    """Request to run a projection."""

    assumptions: Assumptions
