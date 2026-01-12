"""
LLM-based parser for converting natural language to structured assumptions.

Uses Claude to extract actuarial parameters from free-form text input.
"""

import os
import json
import anthropic
from .models import Assumptions, ParseResponse


EXTRACTION_PROMPT = """You are an actuarial assumption parser. Extract structured parameters from the user's natural language description of a term life insurance product.

Extract these parameters:
- num_policies: Number of policies (integer)
- sum_assured: Sum assured per policy in GBP (number, convert k/K to thousands, m/M to millions)
- term_years: Policy term in years (integer)
- entry_age: Entry age in years (integer)
- interest_rate: Annual interest rate as a decimal (e.g., 3% becomes 0.03)
- monthly_premium: Monthly premium per policy in GBP (number)

Rules:
- If a value is not specified, use these defaults:
  - mortality_table: "ELT17_MALES" (always use this for "standard mortality")
- Convert all currency values to plain numbers (e.g., "£100k" -> 100000)
- Convert percentages to decimals (e.g., "3%" -> 0.03)
- If annual premium is given, divide by 12 for monthly premium

Respond with ONLY a valid JSON object with these exact keys:
{
  "num_policies": <int>,
  "sum_assured": <float>,
  "term_years": <int>,
  "entry_age": <int>,
  "interest_rate": <float>,
  "monthly_premium": <float>
}

Do not include any explanation, just the JSON."""


async def parse_natural_language(text: str) -> ParseResponse:
    """
    Parse natural language input into structured assumptions using Claude.

    Args:
        text: Natural language description of actuarial assumptions

    Returns:
        ParseResponse with either parsed assumptions or an error message
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return ParseResponse(
            success=False,
            error="ANTHROPIC_API_KEY environment variable not set",
            raw_input=text
        )

    client = anthropic.Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": f"{EXTRACTION_PROMPT}\n\nUser input: {text}"
                }
            ]
        )

        # Extract the response text
        response_text = message.content[0].text.strip()

        # Try to parse as JSON
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])

        parsed_data = json.loads(response_text)

        # Validate and create Assumptions object
        assumptions = Assumptions(**parsed_data)

        return ParseResponse(
            success=True,
            assumptions=assumptions,
            raw_input=text
        )

    except json.JSONDecodeError as e:
        return ParseResponse(
            success=False,
            error=f"Failed to parse LLM response as JSON: {str(e)}",
            raw_input=text
        )
    except ValueError as e:
        return ParseResponse(
            success=False,
            error=f"Invalid assumptions: {str(e)}",
            raw_input=text
        )
    except anthropic.APIError as e:
        return ParseResponse(
            success=False,
            error=f"API error: {str(e)}",
            raw_input=text
        )
