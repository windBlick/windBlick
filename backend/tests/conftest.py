"""Shared test fixtures."""

import pytest
from fastapi.testclient import TestClient

from wind_turbine_visualization.main import create_app


@pytest.fixture
def client():
    """Return a test client with a fresh app instance."""
    app = create_app()
    return TestClient(app)
