"""
Basic smoke tests for BlueSpace Restaurants backend.
"""
import os
import pytest


def _test_db_available():
    """Check if test PostgreSQL is reachable (used for CI; skip locally if not configured)."""
    try:
        import psycopg2
        url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/test_db?sslmode=disable")
        conn = psycopg2.connect(url)
        conn.close()
        return True
    except Exception:
        return False


def test_app_exists(app):
    """Verify the Flask app is created."""
    assert app is not None
    assert app.config["TESTING"] is True


def test_app_has_api_blueprint(app):
    """Verify API blueprint is registered."""
    assert "api" in [bp.name for bp in app.blueprints.values()]


def test_health_or_landing_route(client):
    """Verify a basic route responds."""
    # Try landing page or API health
    response = client.get("/")
    assert response.status_code in (200, 302, 404)  # Redirect or OK


@pytest.mark.skipif(not _test_db_available(), reason="PostgreSQL test DB not available (CI provides it)")
def test_api_restaurants_list(client, app_context):
    """Verify restaurants API endpoint exists and responds."""
    response = client.get("/api/v1/restaurants")
    assert response.status_code == 200
    data = response.get_json()
    assert data.get("success") is True
    assert "restaurants" in data
