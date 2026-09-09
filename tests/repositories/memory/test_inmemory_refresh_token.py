import uuid
from datetime import timedelta

import pytest

from src.fastapi_auth_lib.core.utils import _now
from src.fastapi_auth_lib.models.refresh_token import RefreshToken
from src.fastapi_auth_lib.repositories.memory.async_refresh_token import (
    InMemoryAsyncRefreshTokenRepository,
)


@pytest.fixture
def refresh_repo():
    """Create a fresh in-memory refresh token repository."""
    return InMemoryAsyncRefreshTokenRepository()


def _make_token(user_id: uuid.UUID | None = None, raw: str = "raw-token") -> RefreshToken:
    """Build a RefreshToken with a hashed value."""
    import hashlib
    return RefreshToken(
        user_id=user_id or uuid.uuid4(),
        token_hash=hashlib.sha256(raw.encode()).hexdigest(),
        expires_at=_now() + timedelta(days=7),
    )


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_assigns_incrementing_ids(refresh_repo):
    t1 = await refresh_repo.create_refresh_token(_make_token())
    t2 = await refresh_repo.create_refresh_token(_make_token())

    assert t1.refresh_token_id == 1
    assert t2.refresh_token_id == 2


@pytest.mark.asyncio
async def test_create_stores_fields(refresh_repo):
    user_id = uuid.uuid4()
    token = _make_token(user_id=user_id, raw="my-secret")

    created = await refresh_repo.create_refresh_token(token)

    assert created.user_id == user_id
    assert created.token_hash == token.token_hash
    assert created.expires_at == token.expires_at
    assert created.created_at is not None


@pytest.mark.asyncio
async def test_create_returns_defensive_copy(refresh_repo):
    """Mutating the returned token must not affect the stored one."""
    created = await refresh_repo.create_refresh_token(_make_token(raw="original"))

    created.token_hash = "tampered"

    fetched = await refresh_repo.find_refresh_token_by_hash(created.token_hash)
    assert fetched is None  # "tampered" was never stored


# ---------------------------------------------------------------------------
# FIND BY HASH
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_find_by_hash_returns_token(refresh_repo):
    token = _make_token(raw="find-me")
    created = await refresh_repo.create_refresh_token(token)

    fetched = await refresh_repo.find_refresh_token_by_hash(created.token_hash)

    assert fetched is not None
    assert fetched.refresh_token_id == created.refresh_token_id
    assert fetched.user_id == created.user_id


@pytest.mark.asyncio
async def test_find_by_hash_missing_returns_none(refresh_repo):
    result = await refresh_repo.find_refresh_token_by_hash("nonexistent-hash")
    assert result is None


@pytest.mark.asyncio
async def test_find_by_hash_returns_defensive_copy(refresh_repo):
    """Mutating the fetched token must not affect the stored one."""
    token = _make_token(raw="copy-check")
    await refresh_repo.create_refresh_token(token)

    fetched = await refresh_repo.find_refresh_token_by_hash(token.token_hash)
    fetched.user_id = uuid.uuid4()  # mutate the copy

    fetched_again = await refresh_repo.find_refresh_token_by_hash(token.token_hash)
    assert fetched_again.user_id == token.user_id  # stored value unchanged


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_removes_token(refresh_repo):
    created = await refresh_repo.create_refresh_token(_make_token())

    await refresh_repo.delete_refresh_token(created.refresh_token_id)

    assert await refresh_repo.find_refresh_token_by_hash(created.token_hash) is None


@pytest.mark.asyncio
async def test_delete_missing_is_noop(refresh_repo):
    """Deleting a non-existent ID must not raise."""
    await refresh_repo.delete_refresh_token(99999)


# ---------------------------------------------------------------------------
# DELETE ALL FOR USER
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_all_for_user_removes_only_that_users_tokens(refresh_repo):
    user1 = uuid.uuid4()
    user2 = uuid.uuid4()

    t1 = await refresh_repo.create_refresh_token(_make_token(user_id=user1, raw="u1-a"))
    t2 = await refresh_repo.create_refresh_token(_make_token(user_id=user1, raw="u1-b"))
    t3 = await refresh_repo.create_refresh_token(_make_token(user_id=user2, raw="u2-a"))

    await refresh_repo.delete_all_for_user(user1)

    assert await refresh_repo.find_refresh_token_by_hash(t1.token_hash) is None
    assert await refresh_repo.find_refresh_token_by_hash(t2.token_hash) is None
    assert await refresh_repo.find_refresh_token_by_hash(t3.token_hash) is not None


@pytest.mark.asyncio
async def test_delete_all_for_user_noop_when_no_tokens(refresh_repo):
    """Deleting all tokens for a user with none must not raise."""
    await refresh_repo.delete_all_for_user(uuid.uuid4())


# ---------------------------------------------------------------------------
# MULTIPLE SESSIONS PER USER
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_user_can_have_multiple_sessions(refresh_repo):
    """A user with phone + laptop gets one refresh token per device."""
    user_id = uuid.uuid4()

    t1 = await refresh_repo.create_refresh_token(_make_token(user_id=user_id, raw="phone"))
    t2 = await refresh_repo.create_refresh_token(_make_token(user_id=user_id, raw="laptop"))

    assert t1.refresh_token_id != t2.refresh_token_id
    assert t1.user_id == t2.user_id

    # Both are independently retrievable
    assert await refresh_repo.find_refresh_token_by_hash(t1.token_hash) is not None
    assert await refresh_repo.find_refresh_token_by_hash(t2.token_hash) is not None
