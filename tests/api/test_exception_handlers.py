import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.fastapi_auth_lib.api.exception_handlers import register_exception_handlers
from src.fastapi_auth_lib.api.schemas.responses import ErrorDetail
from src.fastapi_auth_lib.core.exceptions import AuthenticationException
from src.fastapi_auth_lib.core.exceptions import DuplicateEntityException
from src.fastapi_auth_lib.core.exceptions import EntityNotFoundException
from src.fastapi_auth_lib.core.exceptions import TokenException


@pytest.fixture
def app():
    """Create a FastAPI app with registered exception handlers."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/not-found")
    async def raise_not_found():
        raise EntityNotFoundException("User", "not found")

    @app.get("/duplicate")
    async def raise_duplicate():
        raise DuplicateEntityException("User", "email already exists")

    @app.get("/auth-error")
    async def raise_auth():
        raise AuthenticationException("Invalid credentials")

    @app.get("/token-error")
    async def raise_token():
        raise TokenException("Token expired")

    return app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return TestClient(app)


def error_response(description: str):
    """Expected JSON response body."""
    return {"description": description}


class TestRegisterExceptionHandlers:
    """Tests for exception handler registration and responses."""

    def test_entity_not_found_handler(self, client):
        """Should return 404 with correct description."""
        response = client.get("/not-found")
        assert response.status_code == 404
        assert response.json() == error_response("not found")

    def test_duplicate_entity_handler(self, client):
        """Should return 409 with correct description."""
        response = client.get("/duplicate")
        assert response.status_code == 409
        assert response.json() == error_response("email already exists")

    def test_authentication_exception_handler(self, client):
        """Should return 401 with correct description."""
        response = client.get("/auth-error")
        assert response.status_code == 401
        assert response.json() == error_response("Invalid credentials")

    def test_token_exception_handler(self, client):
        """Should return 401 with correct description."""
        response = client.get("/token-error")
        assert response.status_code == 401
        assert response.json() == error_response("Token expired")

    def test_handler_returns_error_detail_model(self, client):
        """Response JSON should match ErrorDetail schema."""
        response = client.get("/not-found")
        # Validate with Pydantic
        ErrorDetail(**response.json())  # should not raise

    def test_empty_description(self, app):
        """Handlers should work with empty description."""

        @app.get("/empty")
        async def raise_empty():
            raise EntityNotFoundException("Item", "")

        client = TestClient(app)
        response = client.get("/empty")
        assert response.status_code == 404
        assert response.json() == error_response("")
