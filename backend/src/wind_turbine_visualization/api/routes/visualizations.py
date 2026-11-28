"""HTTP adapter for the windBlick visualization pipeline."""

import logging
from http import HTTPStatus
from threading import BoundedSemaphore
from uuid import uuid4

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.requests import ClientDisconnect

from wind_turbine_visualization.api.multipart import VisualizationUpload, read_upload
from wind_turbine_visualization.api.problems import VisualizationProblem
from wind_turbine_visualization.api.visualization import render_visualization

router = APIRouter(prefix="/api/v0", tags=["visualizations"])
logger = logging.getLogger(__name__)
RENDER_SLOTS = BoundedSemaphore(2)
NO_STORE = {"Cache-Control": "no-store"}


def _problem(problem: VisualizationProblem, request_id: str) -> JSONResponse:
    content = {
        "type": "about:blank",
        "title": HTTPStatus(problem.status).phrase,
        "status": problem.status,
        "code": problem.code,
        "detail": str(problem),
        "errors": problem.errors,
        "request_id": request_id,
    }
    if problem.part is not None:
        content["part"] = problem.part
    return JSONResponse(
        status_code=problem.status,
        media_type="application/problem+json",
        content=content,
        headers=NO_STORE,
    )


def _render(upload: VisualizationUpload, request_id: str) -> JSONResponse:
    if not RENDER_SLOTS.acquire(blocking=False):
        raise VisualizationProblem(
            503, "RENDER_CAPACITY_EXCEEDED", "The renderer is busy. Try again shortly."
        )
    try:
        return JSONResponse(render_visualization(upload, request_id), headers=NO_STORE)
    finally:
        RENDER_SLOTS.release()


@router.post(
    "/visualizations",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["image", "parameters"],
                        "properties": {
                            "image": {"type": "string", "format": "binary"},
                            "parameters": {"type": "string", "format": "binary"},
                        },
                        "additionalProperties": False,
                    },
                    "encoding": {
                        "image": {"contentType": "image/jpeg, image/png"},
                        "parameters": {"contentType": "application/json"},
                    },
                }
            },
        }
    },
)
async def create_visualization(request: Request) -> JSONResponse:
    """Render a photo using a multipart image and its v0.1 parameter document."""
    request_id = uuid4().hex
    try:
        upload = await read_upload(
            request.headers.get("content-type", ""), request.stream()
        )
        return await run_in_threadpool(_render, upload, request_id)
    except VisualizationProblem as exc:
        return _problem(exc, request_id)
    except ClientDisconnect:
        return _problem(
            VisualizationProblem(400, "INVALID_MULTIPART", "The upload ended early."),
            request_id,
        )
    except Exception as exc:
        logger.error("Visualization %s failed (%s)", request_id, type(exc).__name__)
        return _problem(
            VisualizationProblem(
                500, "INTERNAL_ERROR", "The visualization could not be rendered."
            ),
            request_id,
        )
