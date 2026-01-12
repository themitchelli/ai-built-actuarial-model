"""
FastAPI application for the Actuarial Model Projection Tool.

Endpoints:
- GET / : Serve the web interface
- POST /api/parse : Parse natural language to structured assumptions
- POST /api/project : Run a projection with given assumptions
- POST /api/export : Get CSV export of projection
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
import io

from .models import (
    ParseRequest, ParseResponse, ProjectRequest, Assumptions,
    ProjectionResult
)
from .llm_parser import parse_natural_language
from .projection_engine import run_projection, projection_to_csv

app = FastAPI(
    title="Actuarial Model Projection Tool",
    description="A web-based tool for running term life insurance projections",
    version="1.0.0"
)


@app.get("/")
async def serve_index():
    """Serve the main web interface."""
    return FileResponse("static/index.html")


@app.post("/api/parse", response_model=ParseResponse)
async def parse_assumptions(request: ParseRequest):
    """
    Parse natural language input into structured assumptions.

    Example input:
    "1,000 policies, £100k sum assured, 10-year term, age 40, standard mortality, 3% interest, £50 monthly premium"
    """
    result = await parse_natural_language(request.text)
    return result


@app.post("/api/project", response_model=ProjectionResult)
async def run_projection_endpoint(request: ProjectRequest):
    """
    Run a projection with the given assumptions.

    Returns month-by-month cashflow projections.
    """
    try:
        result = run_projection(request.assumptions)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/project-from-text", response_model=ProjectionResult)
async def run_projection_from_text(request: ParseRequest):
    """
    Parse natural language and run projection in one step.

    Combines /api/parse and /api/project for convenience.
    """
    parse_result = await parse_natural_language(request.text)

    if not parse_result.success:
        raise HTTPException(status_code=400, detail=parse_result.error)

    result = run_projection(parse_result.assumptions)
    return result


@app.post("/api/export")
async def export_csv(request: ProjectRequest):
    """
    Run projection and return CSV file download.
    """
    try:
        result = run_projection(request.assumptions)
        csv_content = projection_to_csv(result)

        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=projection.csv"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Mount static files (for any additional assets)
app.mount("/static", StaticFiles(directory="static"), name="static")
