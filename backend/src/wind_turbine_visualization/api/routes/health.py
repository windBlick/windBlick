"""Health check endpoint for liveness monitoring."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def get_health() -> dict[str, str]:
    """Report that the service is running.

    Returns:
        A static status payload ``{"status": "ok"}``.
    """
    return {"status": "ok"}
