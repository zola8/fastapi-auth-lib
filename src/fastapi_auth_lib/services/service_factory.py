from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.fastapi_auth_lib.repositories.memory.async_auth_identity import InMemoryAsyncAuthIdentityRepository
from src.fastapi_auth_lib.repositories.memory.async_user_profile import InMemoryAsyncUserProfileRepository
from src.fastapi_auth_lib.repositories.sql.async_auth_identity import SqlAsyncAuthIdentityRepository
from src.fastapi_auth_lib.repositories.sql.async_user_profile import SqlAsyncUserProfileRepository
from src.fastapi_auth_lib.services.async_auth_service import AsyncAuthService
from src.fastapi_auth_lib.services.async_user_service import AsyncUserService
from src.fastapi_auth_lib.services.password_hasher.argon2_hasher import Argon2PasswordHasher


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
        self._hasher = Argon2PasswordHasher()
        self._features: dict[str, Any] = {}

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

    def build(self) -> AsyncAuthService:
        if self._user_service is None:
            self._user_service = UserServiceBuilder().build()
        if self._identity_repo is None:
            self._identity_repo = InMemoryAsyncAuthIdentityRepository()
        return AsyncAuthService(
            user_service=self._user_service,
            identity_repo=self._identity_repo,
            password_hasher=self._hasher,
            features=self._features,
        )
