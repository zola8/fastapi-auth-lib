from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Callable

from fastapi import FastAPI

from src.fastapi_auth_lib.api.exception_handlers import register_exception_handlers
from src.fastapi_auth_lib.api.routers.admin import router as admin_router
from src.fastapi_auth_lib.api.routers.auth import router as auth_router
from src.fastapi_auth_lib.api.routers.users import router as user_router
from src.fastapi_auth_lib.core.database import create_tables
from src.fastapi_auth_lib.core.database import dispose_engine
from src.fastapi_auth_lib.services.async_auth_service import AsyncAuthService
from src.fastapi_auth_lib.services.async_user_service import AsyncUserService
from src.fastapi_auth_lib.services.password_hasher.plain_text_hasher import PlaintextHasher
from src.fastapi_auth_lib.services.service_factory import AuthServiceBuilder
from src.fastapi_auth_lib.services.service_factory import UserServiceBuilder
from src.fastapi_auth_lib.services.token.jwt_token_service import DEFAULT_ACCESS_TTL
from src.fastapi_auth_lib.services.token.jwt_token_service import DEFAULT_ACTIVATION_TTL
from src.fastapi_auth_lib.services.token.jwt_token_service import DEFAULT_REFRESH_TTL


class AppBuilder:
    """
    Fluent builder for assembling the FastAPI application.

    Usage:
        app = (
            AppBuilder()
            .with_auth_router()
            .with_users_router()
            .with_admin_router()
            .build()
        )
    """

    def __init__(self) -> None:
        self._title: str = "fastapi-auth-lib"
        self._version: str = "0.1.7"
        self._api_prefix: str = "/api/v1"
        self._routers: list[tuple] = []  # (router, prefix, tags)
        self._exception_handlers: bool = True
        self._lifespan: Callable | None = None
        self._health_check: bool = True
        self._user_service: AsyncUserService | None = None
        self._auth_service: AsyncAuthService | None = None
        self._jwt_config: dict | None = None
        self._sql_mode: bool = False

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    def with_title(self, title: str) -> "AppBuilder":
        self._title = title
        return self

    def with_version(self, version: str) -> "AppBuilder":
        self._version = version
        return self

    def with_api_prefix(self, prefix: str) -> "AppBuilder":
        self._api_prefix = prefix
        return self

    # ------------------------------------------------------------------
    # Service configuration
    # ------------------------------------------------------------------
    def with_in_memory_services(self) -> "AppBuilder":
        """Build and use in-memory services (the default)."""
        self._sql_mode = False
        self._user_service = None
        self._auth_service = None
        return self

    def with_sql_services(self) -> "AppBuilder":
        """
        SQL mode: services are built per-request from the session dependency.
        app.state services are left as None so dependencies know to build fresh.
        """
        self._sql_mode = True
        self._user_service = None
        self._auth_service = None
        # TODO check password hasher with sql?

        # Wrap the original lifespan (with create tables + dispose engine)
        original_lifespan = self._lifespan

        @asynccontextmanager
        async def sql_lifespan(app: FastAPI):
            await create_tables()
            if original_lifespan:
                async with original_lifespan(app):
                    yield
            else:
                yield
            await dispose_engine()

        self._lifespan = sql_lifespan

        return self

    def with_services(
        self,
        user_service: AsyncUserService,
        auth_service: AsyncAuthService,
    ) -> "AppBuilder":
        """Inject pre-built services."""
        self._user_service = user_service
        self._auth_service = auth_service
        return self

    # ------------------------------------------------------------------
    # JWT configuration
    # ------------------------------------------------------------------
    def with_jwt(
        self,
        secret: str,
        issuer: str = "fastapi-auth-lib",
        algorithm: str = "HS256",
        access_ttl: timedelta = DEFAULT_ACCESS_TTL,
        refresh_ttl: timedelta = DEFAULT_REFRESH_TTL,
        activation_ttl: timedelta = DEFAULT_ACTIVATION_TTL,
    ) -> "AppBuilder":
        """Enable JWT tokens for the auth service (both in-memory and SQL modes)."""
        self._jwt_config = {
            "secret": secret,
            "issuer": issuer,
            "algorithm": algorithm,
            "access_ttl": access_ttl,
            "refresh_ttl": refresh_ttl,
            "activation_ttl": activation_ttl,
        }
        return self
    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------
    def with_auth_router(self, prefix: str | None = None) -> "AppBuilder":
        self._routers.append((
            auth_router,
            prefix or self._api_prefix,
            ["Authentication"],
        ))
        return self

    def with_users_router(self, prefix: str | None = None) -> "AppBuilder":
        self._routers.append((
            user_router,
            prefix or self._api_prefix,
            ["Users"],
        ))
        return self

    def with_admin_router(self, prefix: str | None = None) -> "AppBuilder":
        self._routers.append((
            admin_router,
            prefix or self._api_prefix,
            ["Admin"],
        ))
        return self

    def with_router(self, router, prefix: str | None = None) -> "AppBuilder":
        """Register a custom router not part of the library defaults."""
        self._routers.append((router, prefix or self._api_prefix, []))
        return self

    # ------------------------------------------------------------------
    # Features
    # ------------------------------------------------------------------
    def with_exception_handlers(self, enabled: bool = True) -> "AppBuilder":
        self._exception_handlers = enabled
        return self

    def with_lifespan(self, lifespan: Callable) -> "AppBuilder":
        self._lifespan = lifespan
        return self

    def with_health_check(self, enabled: bool = True) -> "AppBuilder":
        self._health_check = enabled
        return self

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------
    def build(self) -> FastAPI:
        # In-memory: build services now
        if not self._sql_mode and self._user_service is None:
            user_service = UserServiceBuilder().build()
            auth_builder = (
                AuthServiceBuilder()
                .with_user_service(user_service)
                .with_password_hasher(PlaintextHasher())
            )
            if self._jwt_config is not None:
                auth_builder = auth_builder.with_jwt(**self._jwt_config)
            self._user_service = user_service
            self._auth_service = auth_builder.build()

        app = FastAPI(
            title=self._title,
            version=self._version,
            lifespan=self._lifespan,
        )

        # Store services on app.state
        app.state.user_service = self._user_service
        app.state.auth_service = self._auth_service
        app.state.jwt_config = self._jwt_config

        if self._exception_handlers:
            register_exception_handlers(app)

        for router, prefix, _tags in self._routers:
            app.include_router(router, prefix=prefix)

        if self._health_check:
            @app.get("/", tags=["Health"])
            async def health_check():
                return {"status": "ok"}

        return app
