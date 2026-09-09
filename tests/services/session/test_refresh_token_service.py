import hashlib
import uuid
from datetime import timedelta

import pytest

from src.fastapi_auth_lib.core.exceptions import TokenException
from src.fastapi_auth_lib.repositories.memory.async_refresh_token import InMemoryAsyncRefreshTokenRepository
from src.fastapi_auth_lib.services.session.refresh_token_service import RefreshTokenService
from src.fastapi_auth_lib.services.token.jwt_token_service import JwtTokenService
from tests.conftest import TEST_ISSUER
from tests.conftest import TEST_SECRET


# ---------------------------------------------------------------------------
# ISSUE
# ---------------------------------------------------------------------------
class TestIssue:
    @pytest.mark.asyncio
    async def test_returns_jwt_string(self, refresh_service):
        user_id = uuid.uuid4()
        token = await refresh_service.issue_refresh_token(user_id)

        assert isinstance(token, str)
        assert token.count(".") == 2  # JWT has three dot-separated parts

    @pytest.mark.asyncio
    async def test_stores_hash_in_repo(self, refresh_service, refresh_token_repo):
        user_id = uuid.uuid4()
        token = await refresh_service.issue_refresh_token(user_id)

        expected_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        stored = await refresh_token_repo.find_refresh_token_by_hash(expected_hash)

        assert stored is not None
        assert stored.user_id == user_id

    @pytest.mark.asyncio
    async def test_stores_correct_expiry(self, refresh_service, refresh_token_repo):
        user_id = uuid.uuid4()
        token = await refresh_service.issue_refresh_token(user_id)

        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        stored = await refresh_token_repo.find_refresh_token_by_hash(token_hash)

        assert stored.expires_at is not None
        assert stored.expires_at > stored.created_at

    @pytest.mark.asyncio
    async def test_multiple_tokens_create_multiple_sessions(self, refresh_service):
        user_id = uuid.uuid4()

        token1 = await refresh_service.issue_refresh_token(user_id)
        token2 = await refresh_service.issue_refresh_token(user_id)

        assert token1 != token2

        uid1 = await refresh_service.verify_refresh_token(token1)
        uid2 = await refresh_service.verify_refresh_token(token2)
        assert uid1 == user_id
        assert uid2 == user_id

    @pytest.mark.asyncio
    async def test_raw_token_is_never_stored(self, refresh_service, refresh_token_repo):
        """Only the hash is persisted, never the raw token."""
        user_id = uuid.uuid4()
        token = await refresh_service.issue_refresh_token(user_id)

        # Trying to find by the raw token itself should return nothing
        stored = await refresh_token_repo.find_refresh_token_by_hash(token)
        assert stored is None


# ---------------------------------------------------------------------------
# VERIFY
# ---------------------------------------------------------------------------
class TestVerify:
    @pytest.mark.asyncio
    async def test_valid_token_returns_user_id(self, refresh_service):
        user_id = uuid.uuid4()
        token = await refresh_service.issue_refresh_token(user_id)

        result = await refresh_service.verify_refresh_token(token)
        assert result == user_id

    @pytest.mark.asyncio
    async def test_invalid_jwt_raises(self, refresh_service):
        with pytest.raises(TokenException):
            await refresh_service.verify_refresh_token("not.a.valid.jwt")

    @pytest.mark.asyncio
    async def test_empty_string_raises(self, refresh_service):
        with pytest.raises(TokenException):
            await refresh_service.verify_refresh_token("")

    @pytest.mark.asyncio
    async def test_none_raises(self, refresh_service):
        with pytest.raises(TokenException):
            await refresh_service.verify_refresh_token(None)

    @pytest.mark.asyncio
    async def test_access_token_cannot_be_used_as_refresh(self, refresh_service, token_service):
        user_id = uuid.uuid4()
        access_token = token_service.create_access_token(user_id)

        with pytest.raises(TokenException):
            await refresh_service.verify_refresh_token(access_token)

    @pytest.mark.asyncio
    async def test_activation_token_cannot_be_used_as_refresh(self, refresh_service, token_service):
        user_id = uuid.uuid4()
        activation_token = token_service.create_activation_token(user_id)

        with pytest.raises(TokenException):
            await refresh_service.verify_refresh_token(activation_token)

    @pytest.mark.asyncio
    async def test_revoked_token_raises(self, refresh_service):
        user_id = uuid.uuid4()
        token = await refresh_service.issue_refresh_token(user_id)

        await refresh_service.revoke_refresh_token(token)

        with pytest.raises(TokenException, match="revoked"):
            await refresh_service.verify_refresh_token(token)

    @pytest.mark.asyncio
    async def test_expired_jwt_raises(self):
        """Token with negative TTL is already expired at creation time."""
        short_service = JwtTokenService(
            secret=TEST_SECRET,
            issuer=TEST_ISSUER,
            refresh_ttl=timedelta(seconds=-1),
        )
        repo = InMemoryAsyncRefreshTokenRepository()
        service = RefreshTokenService(short_service, repo)

        user_id = uuid.uuid4()
        token = await service.issue_refresh_token(user_id)

        with pytest.raises(TokenException, match="expired"):
            await service.verify_refresh_token(token)


# ---------------------------------------------------------------------------
# REVOKE — single session
# ---------------------------------------------------------------------------
class TestRevokeSingle:
    @pytest.mark.asyncio
    async def test_revoke_removes_session(self, refresh_service, refresh_token_repo):
        user_id = uuid.uuid4()
        token = await refresh_service.issue_refresh_token(user_id)

        await refresh_service.revoke_refresh_token(token)

        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        assert await refresh_token_repo.find_refresh_token_by_hash(token_hash) is None

    @pytest.mark.asyncio
    async def test_revoke_is_idempotent(self, refresh_service):
        user_id = uuid.uuid4()
        token = await refresh_service.issue_refresh_token(user_id)

        await refresh_service.revoke_refresh_token(token)
        await refresh_service.revoke_refresh_token(token)  # must not raise

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_is_noop(self, refresh_service):
        await refresh_service.revoke_refresh_token("never.issued.token")

    @pytest.mark.asyncio
    async def test_revoke_does_not_affect_other_sessions(self, refresh_service):
        user_id = uuid.uuid4()
        token1 = await refresh_service.issue_refresh_token(user_id)
        token2 = await refresh_service.issue_refresh_token(user_id)

        await refresh_service.revoke_refresh_token(token1)

        result = await refresh_service.verify_refresh_token(token2)
        assert result == user_id

    @pytest.mark.asyncio
    async def test_revoke_does_not_affect_other_users(self, refresh_service):
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()
        token1 = await refresh_service.issue_refresh_token(user1)
        token2 = await refresh_service.issue_refresh_token(user2)

        await refresh_service.revoke_refresh_token(token1)

        result = await refresh_service.verify_refresh_token(token2)
        assert result == user2


# ---------------------------------------------------------------------------
# REVOKE ALL
# ---------------------------------------------------------------------------
class TestRevokeAll:
    @pytest.mark.asyncio
    async def test_removes_all_sessions_for_user(self, refresh_service):
        user_id = uuid.uuid4()
        token1 = await refresh_service.issue_refresh_token(user_id)
        token2 = await refresh_service.issue_refresh_token(user_id)
        token3 = await refresh_service.issue_refresh_token(user_id)

        await refresh_service.revoke_all_for_user(user_id)

        with pytest.raises(TokenException):
            await refresh_service.verify_refresh_token(token1)
        with pytest.raises(TokenException):
            await refresh_service.verify_refresh_token(token2)
        with pytest.raises(TokenException):
            await refresh_service.verify_refresh_token(token3)

    @pytest.mark.asyncio
    async def test_does_not_affect_other_users(self, refresh_service):
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()
        token1 = await refresh_service.issue_refresh_token(user1)
        token2 = await refresh_service.issue_refresh_token(user2)

        await refresh_service.revoke_all_for_user(user1)

        with pytest.raises(TokenException):
            await refresh_service.verify_refresh_token(token1)
        assert await refresh_service.verify_refresh_token(token2) == user2

    @pytest.mark.asyncio
    async def test_noop_when_no_sessions(self, refresh_service):
        """Revoking all for a user with no sessions must not raise."""
        await refresh_service.revoke_all_for_user(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_user_can_create_new_sessions_after_revoke_all(self, refresh_service):
        user_id = uuid.uuid4()
        await refresh_service.issue_refresh_token(user_id)

        await refresh_service.revoke_all_for_user(user_id)

        # User logs in again — should work
        new_token = await refresh_service.issue_refresh_token(user_id)
        assert await refresh_service.verify_refresh_token(new_token) == user_id


# ---------------------------------------------------------------------------
# ROTATE
# ---------------------------------------------------------------------------
class TestRotate:
    @pytest.mark.asyncio
    async def test_returns_user_id_and_new_token(self, refresh_service):
        user_id = uuid.uuid4()
        old_token = await refresh_service.issue_refresh_token(user_id)

        new_user_id, new_token = await refresh_service.rotate_refresh_token(old_token)

        assert new_user_id == user_id
        assert new_token != old_token
        assert new_token.count(".") == 2  # is a valid JWT

    @pytest.mark.asyncio
    async def test_old_token_is_revoked_after_rotation(self, refresh_service):
        user_id = uuid.uuid4()
        old_token = await refresh_service.issue_refresh_token(user_id)

        await refresh_service.rotate_refresh_token(old_token)

        with pytest.raises(TokenException):
            await refresh_service.verify_refresh_token(old_token)

    @pytest.mark.asyncio
    async def test_new_token_is_verifiable(self, refresh_service):
        user_id = uuid.uuid4()
        old_token = await refresh_service.issue_refresh_token(user_id)

        _, new_token = await refresh_service.rotate_refresh_token(old_token)

        assert await refresh_service.verify_refresh_token(new_token) == user_id

    @pytest.mark.asyncio
    async def test_sequential_rotations_work(self, refresh_service):
        """Multiple consecutive rotations should all succeed."""
        user_id = uuid.uuid4()
        token = await refresh_service.issue_refresh_token(user_id)

        for _ in range(5):
            _, token = await refresh_service.rotate_refresh_token(token)

        assert await refresh_service.verify_refresh_token(token) == user_id

    @pytest.mark.asyncio
    async def test_reuse_detection(self, refresh_service):
        """
        Attacker steals token and uses it first.
        Legitimate user's subsequent attempt fails (token already revoked).
        """
        user_id = uuid.uuid4()
        stolen_token = await refresh_service.issue_refresh_token(user_id)

        # Attacker uses it first
        _, attacker_new_token = await refresh_service.rotate_refresh_token(stolen_token)

        # Legitimate user tries the same (now revoked) token
        with pytest.raises(TokenException, match="revoked"):
            await refresh_service.rotate_refresh_token(stolen_token)

        # Attacker's new token still works
        assert await refresh_service.verify_refresh_token(attacker_new_token) == user_id

    @pytest.mark.asyncio
    async def test_invalid_token_raises(self, refresh_service):
        with pytest.raises(TokenException):
            await refresh_service.rotate_refresh_token("garbage.token.value")

    @pytest.mark.asyncio
    async def test_revoked_token_cannot_be_rotated(self, refresh_service):
        user_id = uuid.uuid4()
        token = await refresh_service.issue_refresh_token(user_id)

        await refresh_service.revoke_refresh_token(token)

        with pytest.raises(TokenException, match="revoked"):
            await refresh_service.rotate_refresh_token(token)
