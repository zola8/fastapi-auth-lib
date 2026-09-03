from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.fastapi_auth_lib.repositories.memory.async_auth_identity import InMemoryAsyncAuthIdentityRepository
from src.fastapi_auth_lib.repositories.memory.async_user_profile import InMemoryAsyncUserProfileRepository
from src.fastapi_auth_lib.repositories.sql.async_auth_identity import SqlAsyncAuthIdentityRepository
from src.fastapi_auth_lib.repositories.sql.async_user_profile import SqlAsyncUserProfileRepository
from src.fastapi_auth_lib.services.async_auth_service import AsyncAuthService
from src.fastapi_auth_lib.services.password_hasher.argon2_hasher import Argon2PasswordHasher


class AuthServiceBuilder:
    """
    Fluent builder for AsyncAuthService.
    """

    def __init__(self) -> None:
        self._user_repo: Any | None = None
        self._identity_repo: Any | None = None
        self._session: AsyncSession | None = None
        self._hasher = Argon2PasswordHasher()
        self._features: dict[str, Any] = {}

    def with_password_hasher(self, hasher) -> "AuthServiceBuilder":
        self._hasher = hasher
        return self

    def with_in_memory(self) -> "AuthServiceBuilder":
        """Use in-memory repositories (default)."""
        self._user_repo = InMemoryAsyncUserProfileRepository()
        self._identity_repo = InMemoryAsyncAuthIdentityRepository()
        self._session = None
        return self

    def with_sql_session(self, session: AsyncSession) -> "AuthServiceBuilder":
        """Use SQLAlchemy async repositories bound to the given session."""
        self._session = session
        self._user_repo = SqlAsyncUserProfileRepository(session)
        self._identity_repo = SqlAsyncAuthIdentityRepository(session)
        return self

    def build(self) -> AsyncAuthService:
        if self._user_repo is None or self._identity_repo is None:
            self.with_in_memory()

        return AsyncAuthService(
            user_repo=self._user_repo,
            identity_repo=self._identity_repo,
            password_hasher=self._hasher,
            session=self._session,
            features=self._features,
        )
