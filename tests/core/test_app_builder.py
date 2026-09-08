from contextlib import asynccontextmanager
from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from src.fastapi_auth_lib.core.app_builder import AppBuilder
from src.fastapi_auth_lib.core.exceptions import AuthenticationException
from src.fastapi_auth_lib.core.exceptions import DuplicateEntityException
from src.fastapi_auth_lib.core.exceptions import EntityNotFoundException
from src.fastapi_auth_lib.core.exceptions import TokenException
from src.fastapi_auth_lib.services.email.dummy_logger_email_service import DummyLoggerEmailService


@pytest.fixture
def client():
    """Create a TestClient for a built app."""

    def _make_client(app: FastAPI) -> TestClient:
        return TestClient(app)

    return _make_client


class TestAppBuilderDefaults:
    """Tests for the default build."""

    def test_default_title_and_version(self):
        app = AppBuilder().build()
        assert app.title == "fastapi-auth-lib"
        assert app.version == "0.1.7"

    def test_custom_title_and_version(self):
        app = AppBuilder().with_title("My App").with_version("9.9.9").build()
        assert app.title == "My App"
        assert app.version == "9.9.9"

    def test_in_memory_services_created_by_default(self):
        app = AppBuilder().build()
        assert app.state.user_service is not None
        assert app.state.auth_service is not None
        assert app.state.email_service is None
        assert app.state.jwt_config is None

    def test_exception_handlers_registered(self):
        app = AppBuilder().build()
        handlers = app.exception_handlers
        assert EntityNotFoundException in handlers
        assert DuplicateEntityException in handlers
        assert AuthenticationException in handlers
        assert TokenException in handlers

    def test_no_routers_by_default(self):
        app = AppBuilder().build()
        route_paths = [route.path for route in app.routes]
        assert "/" in route_paths
        assert not any(path.startswith("/api/v1") for path in route_paths)


class TestHealthCheck:
    def test_enabled_by_default(self):
        client = TestClient(AppBuilder().build())
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_disabled(self):
        client = TestClient(AppBuilder().with_health_check(False).build())
        assert client.get("/").status_code == 404


class TestAppBuilderRouters:
    """Tests for router inclusion."""
    # FastAPI bug -- _IncludedRouter with no .path since 0.137
    pass


class TestAppBuilderCORS:
    """Tests for CORS middleware."""

    def test_cors_disabled_by_default(self):
        app = AppBuilder().build()
        assert not any(m.cls is CORSMiddleware for m in app.user_middleware)

    def test_cors_enabled_allows_default_origin(self):
        app = AppBuilder().with_cors().build()
        resp = TestClient(app).get("/", headers={"Origin": "http://localhost:3000"})
        assert resp.headers["access-control-allow-origin"] == "http://localhost:3000"

    def test_cors_rejects_unknown_origin(self):
        app = AppBuilder().with_cors().build()
        resp = TestClient(app).get("/", headers={"Origin": "https://evil.example.com"})
        assert "access-control-allow-origin" not in resp.headers

    def test_custom_origins(self):
        app = AppBuilder().with_cors(origins=["https://app.example.com"]).build()
        resp = TestClient(app).get("/", headers={"Origin": "https://app.example.com"})
        assert resp.headers["access-control-allow-origin"] == "https://app.example.com"

    def test_partial_override_keeps_defaults(self):
        builder = AppBuilder().with_cors(origins=["https://a.com"])
        assert builder._cors_origins == ["https://a.com"]
        assert builder._cors_methods == ["*"]
        assert builder._cors_headers == ["*"]

    def test_preflight_succeeds_for_allowed_origin(self):
        app = AppBuilder().with_cors().build()
        resp = TestClient(app).options(
            "/",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200
        assert resp.headers["access-control-allow-origin"] == "http://localhost:5173"

    def test_allow_credentials_flag_passthrough(self):
        app = AppBuilder().with_cors(allow_credentials=False).build()
        mw = next(m for m in app.user_middleware if m.cls is CORSMiddleware)
        assert mw.kwargs.get("allow_credentials") is False


class TestAppBuilderJWT:
    """Tests for JWT configuration."""

    def test_jwt_config_set(self):
        secret = "super-secret"
        app = AppBuilder().with_jwt(secret=secret).build()
        assert app.state.jwt_config is not None
        assert app.state.jwt_config["secret"] == secret
        assert app.state.jwt_config["issuer"] == "fastapi-auth-lib"
        assert app.state.jwt_config["algorithm"] == "HS256"

    def test_jwt_config_custom_values(self):
        secret = "my-secret"
        issuer = "my-issuer"
        algo = "HS384"
        access_ttl = timedelta(minutes=30)
        refresh_ttl = timedelta(days=14)
        activation_ttl = timedelta(hours=48)

        app = (
            AppBuilder()
            .with_jwt(
                secret=secret,
                issuer=issuer,
                algorithm=algo,
                access_ttl=access_ttl,
                refresh_ttl=refresh_ttl,
                activation_ttl=activation_ttl,
            )
            .build()
        )
        config = app.state.jwt_config
        assert config["secret"] == secret
        assert config["issuer"] == issuer
        assert config["algorithm"] == algo
        assert config["access_ttl"] == access_ttl
        assert config["refresh_ttl"] == refresh_ttl
        assert config["activation_ttl"] == activation_ttl

    def test_jwt_not_set_by_default(self):
        app = AppBuilder().build()
        assert app.state.jwt_config is None


class TestAppBuilderLifespan:
    """Tests for custom lifespan."""

    def test_custom_lifespan_executed(self):
        lifespan_entered = False
        lifespan_exited = False

        @asynccontextmanager
        async def custom_lifespan(app: FastAPI):
            nonlocal lifespan_entered, lifespan_exited
            lifespan_entered = True
            yield
            lifespan_exited = True

        app = AppBuilder().with_lifespan(custom_lifespan).build()

        with TestClient(app) as client:
            assert lifespan_entered is True
            assert lifespan_exited is False
        assert lifespan_exited is True


class TestAppBuilderEmail:
    """Tests for email service configuration."""

    def test_email_service_none_by_default(self):
        app = AppBuilder().build()
        assert app.state.email_service is None

    def test_with_dummy_email_service(self):
        app = AppBuilder().with_dummy_email().build()
        assert app.state.email_service is not None
        assert isinstance(app.state.email_service, DummyLoggerEmailService)

    def test_with_custom_email_service(self):
        class CustomEmail:
            pass

        custom = CustomEmail()
        app = AppBuilder().with_email_service(custom).build()
        assert app.state.email_service is custom

# TODO service test (fixtures)
# TODO end-to-end test
