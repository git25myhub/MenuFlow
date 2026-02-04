"""
Pytest fixtures for BlueSpace Restaurants backend tests.
"""
import os

# Set test env vars before any app imports (override .env for tests)
os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/test_db?sslmode=disable")
os.environ["SECRET_KEY"] = os.environ.get("SECRET_KEY", "test-secret-key")
os.environ["SIMULATION_MODE"] = "true"

import pytest


@pytest.fixture(scope="session")
def app():
    """Create application for testing."""
    from app import app as flask_app
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False
    # Local PostgreSQL doesn't use SSL - override connect_args for tests
    if "connect_args" in flask_app.config.get("SQLALCHEMY_ENGINE_OPTIONS", {}):
        flask_app.config["SQLALCHEMY_ENGINE_OPTIONS"]["connect_args"]["sslmode"] = "disable"
    return flask_app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Application context for database operations."""
    with app.app_context():
        from extensions import db
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()
