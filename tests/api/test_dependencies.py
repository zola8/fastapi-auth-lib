import uuid
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from src.fastapi_auth_lib.api.dependencies import get_auth_service
from src.fastapi_auth_lib.api.dependencies import get_current_user
from src.fastapi_auth_lib.api.dependencies import get_email_service
from src.fastapi_auth_lib.api.dependencies import get_user_service
from src.fastapi_auth_lib.api.dependencies import require_role
from src.fastapi_auth_lib.core.exceptions import AuthenticationException
from src.fastapi_auth_lib.core.exceptions import PermissionDeniedException
from src.fastapi_auth_lib.models.base import UserRole
from src.fastapi_auth_lib.models.user import UserProfile

TEST_SECRET = "test-secret-which-is-long-enough"
TEST_ISSUER = "test-issuer"

# ---------------------------------------------------------------------------
# require_role
# ---------------------------------------------------------------------------
class TestRequireRole:
    def _make_user(self, roles: list[UserRole]) -> UserProfile:
        return UserProfile(
            user_id=uuid.uuid4(),
            email="test@example.com",
            roles=roles,
        )

    @pytest.mark.asyncio
    async def test_allows_user_with_matching_role(self):
        checker = require_role("admin")
        user = self._make_user([UserRole.ADMIN])

        result = await checker(user)
        assert result == user

    @pytest.mark.asyncio
    async def test_rejects_user_without_matching_role(self):
        checker = require_role("admin")
        user = self._make_user([UserRole.USER])

        with pytest.raises(PermissionDeniedException):
            await checker(user)

    @pytest.mark.asyncio
    async def test_any_of_multiple_roles_allowed(self):
        checker = require_role("user", "admin")
        user = self._make_user([UserRole.USER])

        result = await checker(user)
        assert result == user

    @pytest.mark.asyncio
    async def test_none_of_multiple_roles_rejected(self):
        # User has USER, but endpoint requires ADMIN (the only other valid role)
        checker = require_role("admin")
        user = self._make_user([UserRole.USER])

        with pytest.raises(PermissionDeniedException):
            await checker(user)

    @pytest.mark.asyncio
    async def test_accepts_enum_values_directly(self):
        checker = require_role(UserRole.ADMIN)
        user = self._make_user([UserRole.ADMIN])

        result = await checker(user)
        assert result == user

    @pytest.mark.asyncio
    async def test_user_with_multiple_roles_matches_one(self):
        checker = require_role("admin")
        user = self._make_user([UserRole.USER, UserRole.ADMIN])

        result = await checker(user)
        assert result == user


# ---------------------------------------------------------------------------
# get_current_user
# ---------------------------------------------------------------------------
class TestGetCurrentUser:
    def _make_request(self, auth_header: str | None):
        request = MagicMock()
        request.headers = {"Authorization": auth_header} if auth_header else {}
        return request

    @pytest.mark.asyncio
    async def test_valid_bearer_token_returns_user(self):
        expected_user = UserProfile(
            user_id=uuid.uuid4(),
            email="alice@example.com",
        )
        auth_service = AsyncMock()
        auth_service.get_user_from_access_token.return_value = expected_user

        request = self._make_request("Bearer valid.jwt.token")

        result = await get_current_user(request, auth_service)

        assert result == expected_user
        auth_service.get_user_from_access_token.assert_awaited_once_with("valid.jwt.token")

    @pytest.mark.asyncio
    async def test_missing_authorization_header_raises(self):
        request = self._make_request(None)
        auth_service = AsyncMock()

        with pytest.raises(AuthenticationException, match="Missing bearer token"):
            await get_current_user(request, auth_service)

    @pytest.mark.asyncio
    async def test_empty_authorization_header_raises(self):
        request = self._make_request("")
        auth_service = AsyncMock()

        with pytest.raises(AuthenticationException):
            await get_current_user(request, auth_service)

    @pytest.mark.asyncio
    async def test_non_bearer_scheme_raises(self):
        request = self._make_request("Basic dXNlcjpwYXNz")
        auth_service = AsyncMock()

        with pytest.raises(AuthenticationException):
            await get_current_user(request, auth_service)

    @pytest.mark.asyncio
    async def test_bearer_with_extra_whitespace_strips_token(self):
        auth_service = AsyncMock()
        auth_service.get_user_from_access_token.return_value = MagicMock()

        request = self._make_request("Bearer   token.with.spaces   ")

        await get_current_user(request, auth_service)
        auth_service.get_user_from_access_token.assert_awaited_once_with("token.with.spaces")


# ---------------------------------------------------------------------------
# get_user_service
# ---------------------------------------------------------------------------
class TestGetUserService:
    @pytest.mark.asyncio
    async def test_returns_singleton_when_present(self):
        singleton_service = MagicMock()
        request = MagicMock()
        request.app.state.user_service = singleton_service
        session = MagicMock()

        result = await get_user_service(request, session)

        assert result is singleton_service

    @pytest.mark.asyncio
    async def test_builds_fresh_when_singleton_is_none(self):
        request = MagicMock()
        request.app.state.user_service = None
        session = MagicMock()

        result = await get_user_service(request, session)

        assert result is not None
        assert result is not request.app.state.user_service


# ---------------------------------------------------------------------------
# get_auth_service
# ---------------------------------------------------------------------------
class TestGetAuthService:
    @pytest.mark.asyncio
    async def test_returns_singleton_when_present(self):
        singleton_service = MagicMock()
        request = MagicMock()
        request.app.state.auth_service = singleton_service
        session = MagicMock()
        user_service = MagicMock()

        result = await get_auth_service(request, session, user_service)

        assert result is singleton_service

    @pytest.mark.asyncio
    async def test_builds_fresh_with_jwt_config(self):
        request = MagicMock()
        request.app.state.auth_service = None
        request.app.state.jwt_config = {
            "secret": TEST_SECRET,
            "issuer": TEST_ISSUER,
        }
        session = MagicMock()
        user_service = MagicMock()

        result = await get_auth_service(request, session, user_service)

        assert result is not None

    @pytest.mark.asyncio
    async def test_builds_fresh_without_jwt_config(self):
        request = MagicMock()
        request.app.state.auth_service = None
        request.app.state.jwt_config = None
        session = MagicMock()
        user_service = MagicMock()

        result = await get_auth_service(request, session, user_service)

        assert result is not None


# ---------------------------------------------------------------------------
# get_email_service
# ---------------------------------------------------------------------------
class TestGetEmailService:
    @pytest.mark.asyncio
    async def test_returns_configured_service(self):
        email_service = MagicMock()
        request = MagicMock()
        request.app.state.email_service = email_service

        result = await get_email_service(request)

        assert result is email_service

    @pytest.mark.asyncio
    async def test_returns_none_when_not_configured(self):
        request = MagicMock()
        request.app.state.email_service = None

        result = await get_email_service(request)

        assert result is None
