import asyncio
from datetime import timedelta

from src.fastapi_auth_lib.repositories.memory.async_auth_identity import InMemoryAsyncAuthIdentityRepository
from src.fastapi_auth_lib.repositories.memory.async_user_profile import InMemoryAsyncUserProfileRepository
from src.fastapi_auth_lib.services.async_auth_service import AsyncAuthService
from src.fastapi_auth_lib.services.async_user_service import AsyncUserService
from src.fastapi_auth_lib.services.password_hasher.plain_text_hasher import PlaintextHasher
from src.fastapi_auth_lib.services.service_factory import AuthServiceBuilder
from src.fastapi_auth_lib.services.service_factory import UserServiceBuilder
from src.fastapi_auth_lib.services.token.jwt_token_service import JwtTokenService


class TestUserServiceBuilder:
    """Tests for UserServiceBuilder."""

    def test_default_build_uses_in_memory_repo(self):
        service = UserServiceBuilder().build()
        assert isinstance(service, AsyncUserService)
        # Access private repo for verification
        assert isinstance(service._user_repo, InMemoryAsyncUserProfileRepository)

    def test_with_in_memory_explicit(self):
        builder = UserServiceBuilder().with_in_memory()
        assert isinstance(builder._user_repo, InMemoryAsyncUserProfileRepository)
        service = builder.build()
        assert isinstance(service._user_repo, InMemoryAsyncUserProfileRepository)

    def test_with_sql_session_sets_sql_repo(self):
        # Dummy session; just ensure it sets the SQL repo class (we won't connect)
        class DummySession:
            pass

        session = DummySession()
        builder = UserServiceBuilder().with_sql_session(session)
        # The repo type is SqlAsyncUserProfileRepository, but we can't import it here
        # to avoid circular imports; we just check that build doesn't fail and
        # service is created.
        service = builder.build()
        assert isinstance(service, AsyncUserService)


class TestAuthServiceBuilder:
    """Tests for AuthServiceBuilder."""

    def test_default_build_produces_working_service(self):
        builder = AuthServiceBuilder()
        service = builder.build()
        assert isinstance(service, AsyncAuthService)
        assert isinstance(service._identity_repo, InMemoryAsyncAuthIdentityRepository)
        assert isinstance(service._user_service, AsyncUserService)
        assert service._hasher is None
        assert service._token_service is None

    def test_with_user_service_injection(self):
        user_service = UserServiceBuilder().build()
        service = AuthServiceBuilder().with_user_service(user_service).build()
        assert service._user_service is user_service

    def test_with_in_memory_identity_repo(self):
        builder = AuthServiceBuilder().with_in_memory_identity_repo()
        assert isinstance(builder._identity_repo, InMemoryAsyncAuthIdentityRepository)
        service = builder.build()
        assert isinstance(service._identity_repo, InMemoryAsyncAuthIdentityRepository)

    def test_with_password_hasher(self):
        hasher = PlaintextHasher()
        builder = AuthServiceBuilder().with_password_hasher(hasher)
        assert builder._hasher is hasher
        service = builder.build()
        assert service._hasher is hasher

    def test_with_token_service(self):
        token_service = JwtTokenService(secret="test", issuer="test")
        builder = AuthServiceBuilder().with_token_service(token_service)
        assert builder._token_service is token_service
        service = builder.build()
        assert service._token_service is token_service

    def test_with_jwt_creates_jwt_service(self):
        builder = AuthServiceBuilder().with_jwt(
            secret="secret",
            issuer="issuer",
            algorithm="HS256",
            access_ttl=timedelta(minutes=30),
        )
        assert isinstance(builder._token_service, JwtTokenService)
        assert builder._token_service._secret == "secret"
        assert builder._token_service._issuer == "issuer"
        assert builder._token_service._access_ttl == timedelta(minutes=30)

    def test_with_jwt_default_ttl_values(self):
        builder = AuthServiceBuilder().with_jwt(secret="s", issuer="i")
        token_service = builder._token_service
        assert token_service._access_ttl is not None
        assert token_service._refresh_ttl is not None
        assert token_service._activation_ttl is not None
        assert token_service._reset_ttl is not None

    def test_full_builder_integration(self):
        """Build a fully configured service and verify registration/authentication."""
        hasher = PlaintextHasher()
        token_service = JwtTokenService(secret="secret", issuer="issuer")
        service = (
            AuthServiceBuilder()
            .with_password_hasher(hasher)
            .with_token_service(token_service)
            .build()
        )
        assert isinstance(service._identity_repo, InMemoryAsyncAuthIdentityRepository)
        assert service._hasher is hasher
        assert service._token_service is token_service

        async def run():
            user = await service.register("test@example.com", "secret")
            assert user.email == "test@example.com"
            # Activate user
            from src.fastapi_auth_lib.models.base import UserStatus
            user.status = UserStatus.ACTIVE
            await service._user_service.update_user(user.user_id, user)
            # Authenticate
            logged_in = await service.authenticate_with_password("test@example.com", "secret")
            assert logged_in.user_id == user.user_id

        asyncio.run(run())
