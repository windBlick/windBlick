"""FastAPI application entry point.

Run the development server from ``backend/`` with::

    uv run fastapi dev src/wind_turbine_visualization/main.py
"""

from fastapi import FastAPI

from wind_turbine_visualization.api.routes import health


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Using a factory keeps app construction explicit and lets tests create
    a fresh, independent app instance.

    Returns:
        The configured FastAPI application.
    """
    app = FastAPI(
        title="Wind Turbine Visualization API",
        version="0.1.0",
    )

    app.include_router(health.router)

    return app


# Module-level instance discovered by `fastapi dev` / `fastapi run` and uvicorn.
app = create_app()
