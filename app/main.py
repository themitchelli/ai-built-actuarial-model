"""
FastAPI application for the Actuarial Model Projection Tool.

Endpoints:
- GET / : Serve the web interface
- GET /activity : Activity dashboard
- GET /execution/{id} : Execution detail page
- POST /api/parse : Parse natural language to structured assumptions
- POST /api/project : Run a projection with given assumptions
- POST /api/export : Get CSV export of projection
- GET /api/executions : List all executions
- GET /api/executions/{id} : Get execution details
"""

import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
import io

from .models import (
    ParseRequest, ParseResponse, ProjectRequest, Assumptions,
    ProjectionResult
)
from .llm_parser import parse_natural_language
from .projection_engine import run_projection, projection_to_csv
from . import database as db

app = FastAPI(
    title="Actuarial Model Projection Tool",
    description="A web-based tool for running term life insurance projections",
    version="1.0.0"
)


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.get("/")
async def serve_index():
    """Serve the main web interface."""
    return FileResponse("static/index.html")


@app.get("/activity")
async def serve_activity():
    """Serve the activity dashboard."""
    return FileResponse("static/activity.html")


@app.get("/execution/{execution_id}")
async def serve_execution(execution_id: str):
    """Serve the execution detail page."""
    return FileResponse("static/execution.html")


@app.post("/api/parse", response_model=ParseResponse)
async def parse_assumptions(request: ParseRequest, req: Request):
    """
    Parse natural language input into structured assumptions.

    Example input:
    "1,000 policies, £100k sum assured, 10-year term, age 40, standard mortality, 3% interest, £50 monthly premium"
    """
    start_time = time.time()
    client_ip = get_client_ip(req)

    result = await parse_natural_language(request.text)

    elapsed_ms = (time.time() - start_time) * 1000

    # Log the execution
    db.log_execution(
        action_type="parse",
        ip_address=client_ip,
        tokens_used=0,  # Would need to modify llm_parser to return this
        elapsed_ms=elapsed_ms,
        input_data={"text": request.text},
        output_data=result.model_dump() if result.success else None,
        success=result.success,
        error_message=result.error if not result.success else None
    )

    return result


@app.post("/api/project", response_model=ProjectionResult)
async def run_projection_endpoint(request: ProjectRequest, req: Request):
    """
    Run a projection with the given assumptions.

    Returns month-by-month cashflow projections.
    """
    start_time = time.time()
    client_ip = get_client_ip(req)

    try:
        result = run_projection(request.assumptions)
        elapsed_ms = (time.time() - start_time) * 1000

        # Log the execution
        db.log_execution(
            action_type="project",
            ip_address=client_ip,
            tokens_used=0,
            elapsed_ms=elapsed_ms,
            input_data=request.assumptions.model_dump(),
            output_data={
                "summary": result.summary.model_dump(),
                "row_count": len(result.rows)
            },
            success=True
        )

        return result
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000

        # Log the error
        db.log_execution(
            action_type="project",
            ip_address=client_ip,
            tokens_used=0,
            elapsed_ms=elapsed_ms,
            input_data=request.assumptions.model_dump(),
            success=False,
            error_message=str(e)
        )

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


@app.get("/api/executions")
async def list_executions(limit: int = 100, offset: int = 0):
    """Get list of all executions."""
    executions = db.get_all_executions(limit=limit, offset=offset)
    total = db.get_execution_count()
    stats = db.get_stats()

    return {
        "executions": executions,
        "total": total,
        "limit": limit,
        "offset": offset,
        "stats": stats
    }


@app.get("/api/executions/{execution_id}")
async def get_execution(execution_id: str):
    """Get details of a specific execution."""
    execution = db.get_execution_by_id(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


# Mount static files (for any additional assets)
app.mount("/static", StaticFiles(directory="static"), name="static")
