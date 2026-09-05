from datetime import timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.fastapi_auth_lib.repositories.memory.async_auth_identity import InMemoryAsyncAuthIdentityRepository
from src.fastapi_auth_lib.repositories.memory.async_user_profile import InMemoryAsyncUserProfileRepository
from src.fastapi_auth_lib.repositories.sql.async_auth_identity import SqlAsyncAuthIdentityRepository
from src.fastapi_auth_lib.repositories.sql.async_user_profile import SqlAsyncUserProfileRepository
from src.fastapi_auth_lib.services.async_auth_service import AsyncAuthService
from src.fastapi_auth_lib.services.async_user_service import AsyncUserService
from src.fastapi_auth_lib.services.password_hasher.protocol import PasswordHasherProtocol
from src.fastapi_auth_lib.services.token.jwt_token_service import DEFAULT_ACCESS_TTL
from src.fastapi_auth_lib.services.token.jwt_token_service import DEFAULT_ACTIVATION_TTL
from src.fastapi_auth_lib.services.token.jwt_token_service import DEFAULT_REFRESH_TTL
from src.fastapi_auth_lib.services.token.jwt_token_service import JwtTokenService
from src.fastapi_auth_lib.services.token.token_protocol import TokenServiceProtocol


class UserServiceBuilder:
    def __init__(self) -> None:
        self._user_repo: Any | None = None

    def with_in_memory(self) -> "UserServiceBuilder":
        self._user_repo = InMemoryAsyncUserProfileRepository()
        return self

    def with_sql_session(self, session: AsyncSession) -> "UserServiceBuilder":
        self._user_repo = SqlAsyncUserProfileRepository(session)
        return self

    def build(self) -> AsyncUserService:
        if self._user_repo is None:
            self.with_in_memory()
        return AsyncUserService(user_repo=self._user_repo)


class AuthServiceBuilder:
    def __init__(self) -> None:
        self._user_service: AsyncUserService | None = None
        self._identity_repo: Any | None = None
        self._hasher: PasswordHasherProtocol | None = None
        self._token_service: TokenServiceProtocol | None = None

    def with_password_hasher(self, hasher) -> "AuthServiceBuilder":
        self._hasher = hasher
        return self

    def with_user_service(self, user_service: AsyncUserService) -> "AuthServiceBuilder":
        self._user_service = user_service
        return self

    def with_in_memory_identity_repo(self) -> "AuthServiceBuilder":
        self._identity_repo = InMemoryAsyncAuthIdentityRepository()
        return self

    def with_sql_session(self, session: AsyncSession) -> "AuthServiceBuilder":
        self._identity_repo = SqlAsyncAuthIdentityRepository(session)
        return self

    def with_token_service(self, token_service: TokenServiceProtocol) -> "AuthServiceBuilder":
        """Inject any TokenServiceProtocol-compatible implementation."""
        self._token_service = token_service
        return self

    def with_jwt(
        self,
        secret: str,
        issuer: str,
        algorithm: str = "HS256",
        access_ttl: timedelta = DEFAULT_ACCESS_TTL,
        refresh_ttl: timedelta = DEFAULT_REFRESH_TTL,
        activation_ttl: timedelta = DEFAULT_ACTIVATION_TTL,
    ) -> "AuthServiceBuilder":
        self._token_service = JwtTokenService(
            secret=secret,
            issuer=issuer,
            algorithm=algorithm,
            access_ttl=access_ttl,
            refresh_ttl=refresh_ttl,
            activation_ttl=activation_ttl,
        )
        return self

    def build(self) -> AsyncAuthService:
        if self._user_service is None:
            self._user_service = UserServiceBuilder().build()
        if self._identity_repo is None:
            self._identity_repo = InMemoryAsyncAuthIdentityRepository()

        return AsyncAuthService(
            user_service=self._user_service,
            identity_repo=self._identity_repo,
            password_hasher=self._hasher,
            token_service=self._token_service,
        )
