"""Tests for the health endpoint."""


def test_health_endpoint_returns_ok(client):
    """GET /health returns 200 and {"status": "ok"}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_route_returns_404(client):
    """GET /unknown returns 404."""
    response = client.get("/unknown")
    assert response.status_code == 404
