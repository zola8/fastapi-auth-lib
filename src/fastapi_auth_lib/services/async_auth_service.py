from typing import Any

from src.fastapi_auth_lib.core.constants import AUTH_IDENTITY_ENTITY
from src.fastapi_auth_lib.core.exceptions import AuthenticationException
from src.fastapi_auth_lib.core.exceptions import DuplicateEntityException
from src.fastapi_auth_lib.core.utils import normalize_email
from src.fastapi_auth_lib.models.auth_identity import AuthIdentity
from src.fastapi_auth_lib.models.base import AuthProvider
from src.fastapi_auth_lib.models.user import UserProfile


class AsyncAuthService:
    """
    Minimal authentication service.

    - Normalization happens here (not in repositories).
    - Commits the session after writes when one is injected (SQL backend).
    - No-op on commit for in-memory backend (session is None).
    """

    def __init__(
        self,
        user_repo: Any,
        identity_repo: Any,
        password_hasher: Any,
        session: Any | None = None,
        features: dict[str, Any] | None = None,
    ) -> None:
        self._user_repo = user_repo
        self._identity_repo = identity_repo
        self._hasher = password_hasher
        self._session = session
        self._features = features or {}

    async def _commit_if_needed(self) -> None:
        if self._session is not None:
            await self._session.commit()

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    async def register(self, email: str, password: str) -> UserProfile:
        normalized_email = normalize_email(email)

        existing = await self._identity_repo.find_auth_identity_by_provider_subject(
            AuthProvider.PASSWORD, normalized_email
        )
        if existing is not None:
            raise DuplicateEntityException(
                entity_type=AUTH_IDENTITY_ENTITY,
                description=f"An account with email '{normalized_email}' already exists",
            )

        hashed = self._hasher.hash_password(password)

        user = await self._user_repo.create_user(
            UserProfile(email=normalized_email)
        )

        await self._identity_repo.create_auth_identity(
            AuthIdentity(
                user_id=user.user_id,
                provider=AuthProvider.PASSWORD,
                provider_subject=normalized_email,
                password_hash=hashed,
            )
        )

        await self._commit_if_needed()
        return user

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------
    async def authenticate(self, email: str, password: str) -> UserProfile:
        normalized_email = normalize_email(email)

        identity = await self._identity_repo.find_auth_identity_by_provider_subject(
            AuthProvider.PASSWORD, normalized_email
        )

        # Same error for missing account and wrong password (no enumeration)
        if identity is None or not self._hasher.verify_password(
            password, identity.password_hash
        ):
            raise AuthenticationException("Invalid credentials")

        user = await self._user_repo.find_user_by_id(identity.user_id)
        if user is None:
            raise AuthenticationException("Invalid credentials")

        return user
