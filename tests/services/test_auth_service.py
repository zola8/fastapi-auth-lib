import pytest

from src.fastapi_auth_lib.core.constants import AUTH_IDENTITY_ENTITY
from src.fastapi_auth_lib.core.exceptions import AuthenticationException
from src.fastapi_auth_lib.core.exceptions import DuplicateEntityException
from src.fastapi_auth_lib.core.exceptions import FeatureNotConfiguredException
from src.fastapi_auth_lib.core.exceptions import TokenException
from src.fastapi_auth_lib.models.base import AuthProvider
from src.fastapi_auth_lib.models.base import UserStatus
from src.fastapi_auth_lib.services.async_auth_service import AsyncAuthService


class TestRegister:
    """Tests for register()."""

    @pytest.mark.asyncio
    async def test_register_success(self, auth_service):
        user = await auth_service.register("user@example.com", "secret")
        assert user.user_id is not None
        assert user.email == "user@example.com"
        assert user.username == "user"
        identity = await auth_service._identity_repo.find_auth_identity_by_user_id(user.user_id)
        assert identity is not None
        assert identity.provider == AuthProvider.PASSWORD
        assert identity.provider_subject == "user@example.com"
        assert identity.password_hash == "secret"  # PlaintextHasher stores raw

    @pytest.mark.asyncio
    async def test_register_email_normalized(self, auth_service):
        user = await auth_service.register("  User@Example.COM  ", "secret")
        assert user.email == "user@example.com"
        assert user.username == "user"

    @pytest.mark.asyncio
    async def test_register_duplicate_email_raises(self, auth_service):
        await auth_service.register("user@example.com", "secret")
        with pytest.raises(DuplicateEntityException) as exc_info:
            await auth_service.register("USER@example.com", "other")
        assert exc_info.value.entity_type == AUTH_IDENTITY_ENTITY

    @pytest.mark.asyncio
    async def test_register_missing_hasher_raises(self, user_service, auth_identity_repo, token_service):
        service = AsyncAuthService(
            user_service=user_service,
            identity_repo=auth_identity_repo,
            password_hasher=None,
            token_service=token_service,
        )
        with pytest.raises(FeatureNotConfiguredException):
            await service.register("user@example.com", "secret")


class TestAuthenticateWithPassword:
    """Tests for authenticate_with_password()."""

    @pytest.mark.asyncio
    async def test_authenticate_success(self, auth_service, user_service):
        user = await auth_service.register("user@example.com", "secret")
        user.status = UserStatus.ACTIVE
        await user_service.update_user(user.user_id, user)

        result = await auth_service.authenticate_with_password("user@example.com", "secret")
        assert result.user_id == user.user_id
        assert result.status == UserStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(self, auth_service, user_service):
        user = await auth_service.register("user@example.com", "secret")
        user.status = UserStatus.ACTIVE
        await user_service.update_user(user.user_id, user)

        with pytest.raises(AuthenticationException):
            await auth_service.authenticate_with_password("user@example.com", "wrong")

    @pytest.mark.asyncio
    async def test_authenticate_unknown_email(self, auth_service):
        with pytest.raises(AuthenticationException):
            await auth_service.authenticate_with_password("unknown@example.com", "secret")

    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self, auth_service):
        await auth_service.register("user@example.com", "secret")
        with pytest.raises(AuthenticationException):
            await auth_service.authenticate_with_password("user@example.com", "secret")

    @pytest.mark.asyncio
    async def test_authenticate_missing_hasher_raises(self, user_service, auth_identity_repo, token_service):
        service = AsyncAuthService(
            user_service=user_service,
            identity_repo=auth_identity_repo,
            password_hasher=None,
            token_service=token_service,
        )
        with pytest.raises(FeatureNotConfiguredException):
            await service.authenticate_with_password("user@example.com", "secret")


class TestActivation:
    """Tests for create_activation_token and activate_account()."""

    @pytest.mark.asyncio
    async def test_activate_account_success(self, auth_service, user_service):
        user = await auth_service.register("user@example.com", "secret")
        token = auth_service.create_activation_token(user)
        activated = await auth_service.activate_account(token)
        assert activated.status == UserStatus.ACTIVE
        fetched = await user_service.get_user(user.user_id)
        assert fetched.status == UserStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_activate_account_already_active_idempotent(self, auth_service, user_service):
        user = await auth_service.register("user@example.com", "secret")
        token = auth_service.create_activation_token(user)
        await auth_service.activate_account(token)
        activated_again = await auth_service.activate_account(token)
        assert activated_again.status == UserStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_activate_account_missing_token_service_raises(self, user_service, auth_identity_repo,
                                                                 password_hasher):
        service = AsyncAuthService(
            user_service=user_service,
            identity_repo=auth_identity_repo,
            password_hasher=password_hasher,
            token_service=None,
        )
        with pytest.raises(FeatureNotConfiguredException):
            await service.activate_account("some-token")

    @pytest.mark.asyncio
    async def test_activate_account_invalid_token_raises(self, auth_service):
        with pytest.raises(TokenException):
            await auth_service.activate_account("invalid-token")


class TestResendActivation:
    """Tests for resend_activation()."""

    @pytest.mark.asyncio
    async def test_resend_activation_inactive_user(self, auth_service):
        user = await auth_service.register("user@example.com", "secret")
        result = await auth_service.resend_activation("user@example.com")
        assert result is not None
        returned_user, token = result
        assert returned_user.user_id == user.user_id
        assert token is not None

    @pytest.mark.asyncio
    async def test_resend_activation_active_user_returns_none(self, auth_service, user_service):
        user = await auth_service.register("user@example.com", "secret")
        user.status = UserStatus.ACTIVE
        await user_service.update_user(user.user_id, user)
        result = await auth_service.resend_activation("user@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_resend_activation_unknown_email_returns_none(self, auth_service):
        result = await auth_service.resend_activation("unknown@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_resend_activation_missing_token_service_raises(self, user_service, auth_identity_repo,
                                                                  password_hasher):
        service = AsyncAuthService(
            user_service=user_service,
            identity_repo=auth_identity_repo,
            password_hasher=password_hasher,
            token_service=None,
        )
        # Need to register first to have an inactive user
        await service.register("user@example.com", "secret")
        with pytest.raises(FeatureNotConfiguredException):
            await service.resend_activation("user@example.com")
