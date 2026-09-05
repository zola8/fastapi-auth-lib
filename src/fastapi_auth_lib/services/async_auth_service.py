from src.fastapi_auth_lib.core.constants import AUTH_IDENTITY_ENTITY
from src.fastapi_auth_lib.core.exceptions import AuthenticationException
from src.fastapi_auth_lib.core.exceptions import DuplicateEntityException
from src.fastapi_auth_lib.core.exceptions import FeatureNotConfiguredException
from src.fastapi_auth_lib.core.utils import normalize_email
from src.fastapi_auth_lib.models.auth_identity import AuthIdentity
from src.fastapi_auth_lib.models.base import AuthProvider
from src.fastapi_auth_lib.models.base import UserStatus
from src.fastapi_auth_lib.models.user import UserProfile
from src.fastapi_auth_lib.services.token.jwt_token_service import TokenPair


class AsyncAuthService:

    def __init__(self,
                 user_service,
                 identity_repo,
                 password_hasher,
                 token_service=None
                 ) -> None:
        self._user_service = user_service
        self._identity_repo = identity_repo
        self._hasher = password_hasher
        self._token_service = token_service

    # ------------------------------------------------------------------
    # Require checks
    # ------------------------------------------------------------------

    def _require_hasher(self):
        if self._hasher is None:
            raise FeatureNotConfiguredException(
                description="Password hasher is not configured. "
                            "Add .with_password_hasher(...) to the builder"
            )
        return self._hasher

    def _require_token_service(self):
        if self._token_service is None:
            raise FeatureNotConfiguredException(
                description="Token service is not configured. "
                            "Add .with_jwt(...) or .with_token_service(...) to the builder."
            )
        return self._token_service

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    async def register(self, email: str, password: str) -> UserProfile:
        hasher = self._require_hasher()
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
                password_hash=hasher.hash_password(password),
            )
        )
        return user

    async def authenticate_with_password(self, email: str, password: str) -> UserProfile:
        hasher = self._require_hasher()
        normalized_email = normalize_email(email)
        identity = await self._identity_repo.find_auth_identity_by_provider_subject(
            AuthProvider.PASSWORD, normalized_email
        )
        if identity is None or not hasher.verify_password(
            password, identity.password_hash
        ):
            raise AuthenticationException("Invalid credentials")

        user = await self._user_service.get_user(identity.user_id)

        if user.status != UserStatus.ACTIVE:
            raise AuthenticationException("Invalid credentials, user status is not ACTIVE")
        return user

    # ------------------------------------------------------------------
    # Activation
    # ------------------------------------------------------------------

    def create_activation_token(self, user: UserProfile) -> str:
        """Issued right after registration; sent to the user by email."""
        return self._require_token_service().create_activation_token(user.user_id)

    async def activate_account(self, token: str) -> UserProfile:
        user_id = self._require_token_service().verify_activation_token(token)
        user = await self._user_service.get_user(user_id)
        if user.status == UserStatus.ACTIVE:
            return user  # idempotent — link re-clicks are safe
        user.status = UserStatus.ACTIVE
        return await self._user_service.update_user(user_id, user)

    # ------------------------------------------------------------------
    # Login tokens
    # ------------------------------------------------------------------
    def create_token_pair(self, user: UserProfile) -> TokenPair:
        """Called by the router after authenticate_with_password succeeds."""
        ts = self._require_token_service()
        return TokenPair(
            access_token=ts.create_access_token(user.user_id),
            refresh_token=ts.create_refresh_token(user.user_id),
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenPair:
        ts = self._require_token_service()
        user_id = ts.verify_refresh_token(refresh_token)
        user = await self._user_service.get_user(user_id)
        if user.status != UserStatus.ACTIVE:
            raise AuthenticationException("Invalid credentials")
        return TokenPair(
            access_token=ts.create_access_token(user_id),
            refresh_token=ts.create_refresh_token(user_id),
        )

    # ------------------------------------------------------------------
    # Protected-route helper (backs your get_current_logged_in_user dep)
    # ------------------------------------------------------------------
    async def get_user_from_access_token(self, token: str) -> UserProfile:
        user_id = self._require_token_service().verify_access_token(token)
        user = await self._user_service.get_user(user_id)
        if user.status != UserStatus.ACTIVE:
            raise AuthenticationException("Invalid credentials")
        return user
