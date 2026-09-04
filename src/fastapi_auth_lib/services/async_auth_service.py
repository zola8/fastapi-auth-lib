from src.fastapi_auth_lib.core.constants import AUTH_IDENTITY_ENTITY
from src.fastapi_auth_lib.core.exceptions import AuthenticationException
from src.fastapi_auth_lib.core.exceptions import DuplicateEntityException
from src.fastapi_auth_lib.core.utils import normalize_email
from src.fastapi_auth_lib.models.auth_identity import AuthIdentity
from src.fastapi_auth_lib.models.base import AuthProvider
from src.fastapi_auth_lib.models.base import UserStatus
from src.fastapi_auth_lib.models.user import UserProfile


class AsyncAuthService:

    def __init__(self, user_service, identity_repo, password_hasher, features=None) -> None:
        self._user_service = user_service
        self._identity_repo = identity_repo
        self._hasher = password_hasher
        self._features = features or {}

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

        user = await self._user_service.create_user(
            UserProfile(
                email=normalized_email,
                username=normalized_email.split("@")[0],
            )
        )

        await self._identity_repo.create_auth_identity(
            AuthIdentity(
                user_id=user.user_id,
                provider=AuthProvider.PASSWORD,
                provider_subject=normalized_email,
                password_hash=self._hasher.hash_password(password),
            )
        )
        return user

    async def authenticate_with_password(self, email: str, password: str) -> UserProfile:
        normalized_email = normalize_email(email)
        identity = await self._identity_repo.find_auth_identity_by_provider_subject(
            AuthProvider.PASSWORD, normalized_email
        )
        if identity is None or not self._hasher.verify_password(
            password, identity.password_hash
        ):
            raise AuthenticationException("Invalid credentials")

        user = await self._user_service.get_user(identity.user_id)

        if user.status != UserStatus.ACTIVE:
            raise AuthenticationException("Invalid credentials, user status is not ACTIVE")
        return user
