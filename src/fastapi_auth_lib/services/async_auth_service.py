import logging
from uuid import UUID

from src.fastapi_auth_lib.core.constants import AUTH_IDENTITY_ENTITY
from src.fastapi_auth_lib.core.exceptions import AuthenticationException
from src.fastapi_auth_lib.core.exceptions import DuplicateEntityException
from src.fastapi_auth_lib.core.exceptions import FeatureNotConfiguredException
from src.fastapi_auth_lib.core.utils import normalize_email
from src.fastapi_auth_lib.models.auth_identity import AuthIdentity
from src.fastapi_auth_lib.models.base import AuthProvider
from src.fastapi_auth_lib.models.base import UserStatus
from src.fastapi_auth_lib.models.user import UserProfile
from src.fastapi_auth_lib.repositories.async_auth_identity import AsyncAuthIdentityRepository
from src.fastapi_auth_lib.services.async_user_service import AsyncUserService
from src.fastapi_auth_lib.services.password_hasher.password_hash_protocol import PasswordHasherProtocol
from src.fastapi_auth_lib.services.token.jwt_token_service import TokenPair
from src.fastapi_auth_lib.services.token.token_protocol import TokenServiceProtocol

logger = logging.getLogger(__name__)


class AsyncAuthService:

    def __init__(
        self,
        user_service: AsyncUserService,
        identity_repo: AsyncAuthIdentityRepository,
        password_hasher: PasswordHasherProtocol | None = None,
        token_service: TokenServiceProtocol | None = None,
        refresh_token_service=None,
    ) -> None:
        self._user_service = user_service
        self._identity_repo = identity_repo
        self._hasher = password_hasher
        self._token_service = token_service
        self._refresh_token_service = refresh_token_service

    # ------------------------------------------------------------------
    # Require checks
    # ------------------------------------------------------------------

    def _require_hasher(self) -> PasswordHasherProtocol:
        if self._hasher is None:
            raise FeatureNotConfiguredException(
                description="Password hasher is not configured. "
                            "Add .with_password_hasher(...) to the builder"
            )
        return self._hasher

    def _require_token_service(self) -> TokenServiceProtocol:
        if self._token_service is None:
            raise FeatureNotConfiguredException(
                description="Token service is not configured. "
                            "Add .with_jwt(...) or .with_token_service(...) to the builder."
            )
        return self._token_service

    def _require_refresh_service(self):
        if self._refresh_token_service is None:
            raise FeatureNotConfiguredException(
                description="Refresh token service is not configured. "
                            "Add .with_refresh_token_service(...) to the builder."
            )
        return self._refresh_token_service

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

    async def create_activation_token(self, user: UserProfile) -> str:
        """Issued right after registration; sent to the user by email."""
        return self._require_token_service().create_activation_token(user.user_id)

    async def activate_account(self, token: str) -> UserProfile:
        user_id = self._require_token_service().verify_activation_token(token)
        user = await self._user_service.get_user(user_id)
        if user.status == UserStatus.ACTIVE:
            logger.debug("user is already active: %s", user)
            return user  # idempotent — link re-clicks are safe
        user.status = UserStatus.ACTIVE

        user = await self._user_service.update_user(user_id, user)
        logger.debug("user activated: %s", user)
        return user

    async def resend_activation(self, email: str) -> tuple[UserProfile, str] | None:
        """
        Returns (user, new_activation_token) if the account exists AND is inactive.
        Returns None otherwise — the caller must NOT reveal which case occurred.
        """
        normalized_email = normalize_email(email)

        identity = await self._identity_repo.find_auth_identity_by_provider_subject(
            AuthProvider.PASSWORD, normalized_email
        )
        if identity is None:
            logger.debug("user has no identity: %s", normalized_email)
            return None

        user = await self._user_service.get_user(identity.user_id)
        if user.status != UserStatus.INACTIVE:
            logger.debug("user is not inactive, no re-send happens. User: %s", user.email)
            return None

        new_token = self._require_token_service().create_activation_token(user.user_id)
        return user, new_token

    # ------------------------------------------------------------------
    # Password reset
    # ------------------------------------------------------------------
    async def request_password_reset(self, email: str) -> tuple[UserProfile, str] | None:
        """
        Returns (user, reset_token) only if the account exists AND is ACTIVE.
        Returns None otherwise — caller must not reveal which case occurred.
        """
        normalized_email = normalize_email(email)

        identity = await self._identity_repo.find_auth_identity_by_provider_subject(
            AuthProvider.PASSWORD, normalized_email
        )
        if identity is None:
            logger.debug("user has no identity: %s", normalized_email)
            return None

        user = await self._user_service.get_user(identity.user_id)
        if user.status != UserStatus.ACTIVE:
            logger.debug("user is not inactive, no re-send happens. User: %s", user.email)
            return None

        reset_token = self._require_token_service().create_reset_token(user.user_id)
        logger.debug("email: %s. reset token: %s", normalized_email, reset_token)
        return user, reset_token

    async def reset_password(self, token: str, new_password: str) -> UserProfile:
        """Verify the reset token and update the password."""
        user_id = self._require_token_service().verify_reset_token(token)

        identity = await self._identity_repo.find_auth_identity_by_user_id(user_id)
        if identity is None:
            raise AuthenticationException("Invalid credentials")

        identity.password_hash = self._hasher.hash_password(new_password)
        await self._identity_repo.update_auth_identity(
            identity.auth_identity_id, identity
        )

        await self.logout_all_sessions(user_id)

        return await self._user_service.get_user(user_id)

    # ------------------------------------------------------------------
    # Login tokens
    # ------------------------------------------------------------------
    async def create_token_pair(self, user: UserProfile) -> TokenPair:
        """Create access + refresh tokens. Refresh token is stored in DB."""
        ts = self._require_token_service()
        rts = self._require_refresh_service()

        access_token = ts.create_access_token(user.user_id)
        refresh_token = await rts.issue_refresh_token(user.user_id)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenPair:
        """
        Verify the refresh token, rotate it (delete old, issue new),
        and return a new token pair.
        """
        ts = self._require_token_service()
        rts = self._require_refresh_service()

        user_id, new_refresh_token = await rts.rotate_refresh_token(refresh_token)

        # Verify user is still active
        user = await self._user_service.get_user(user_id)
        if user.status != UserStatus.ACTIVE:
            # Revoke the newly issued token if user was deactivated between verify and check
            await rts.revoke_refresh_token(new_refresh_token)
            raise AuthenticationException("Invalid credentials")

        new_access_token = ts.create_access_token(user_id)

        return TokenPair(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------
    async def logout(self, refresh_token: str) -> None:
        """Revoke a single refresh token (logout one session)."""
        rts = self._require_refresh_service()
        await rts.revoke_refresh_token(refresh_token)

    async def logout_all_sessions(self, user_id: UUID) -> None:
        """Revoke all refresh tokens for a user (logout everywhere)."""
        rts = self._require_refresh_service()
        await rts.revoke_all_for_user(user_id)

    # ------------------------------------------------------------------
    # Protected-route helper (backs your get_current_user dep)
    # ------------------------------------------------------------------
    async def get_user_from_access_token(self, token: str) -> UserProfile:
        user_id = self._require_token_service().verify_access_token(token)
        user = await self._user_service.get_user(user_id)
        if user.status != UserStatus.ACTIVE:
            raise AuthenticationException("Invalid credentials")
        return user
