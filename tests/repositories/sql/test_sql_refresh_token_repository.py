import hashlib
import uuid
from datetime import timedelta

import pytest

from src.fastapi_auth_lib.core.utils import _now
from src.fastapi_auth_lib.models.refresh_token import RefreshToken
from src.fastapi_auth_lib.models.user import UserProfile


def _token(user_id: uuid.UUID, raw: str = "raw-token") -> RefreshToken:
    return RefreshToken(
        user_id=user_id,
        token_hash=hashlib.sha256(raw.encode()).hexdigest(),
        expires_at=_now() + timedelta(days=7),
    )


async def _create_user(user_repo, email="sess@example.com") -> UserProfile:
    return await user_repo.create_user(UserProfile(email=email))


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_refresh_token_assigns_id(user_auth_refresh_repos):
    user_repo, auth_repo, refresh_repo = user_auth_refresh_repos
    user = await _create_user(user_repo)

    created = await refresh_repo.create_refresh_token(_token(user.user_id))

    assert created.refresh_token_id is not None
    assert created.user_id == user.user_id
    assert created.expires_at > _now()


# ---------------------------------------------------------------------------
# FIND BY HASH
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_find_refresh_token_by_hash_returns_token(user_auth_refresh_repos):
    user_repo, auth_repo, refresh_repo = user_auth_refresh_repos
    user = await _create_user(user_repo)
    created = await refresh_repo.create_refresh_token(_token(user.user_id, "find-me"))

    fetched = await refresh_repo.find_refresh_token_by_hash(created.token_hash)

    assert fetched is not None
    assert fetched.refresh_token_id == created.refresh_token_id


@pytest.mark.asyncio
async def test_find_refresh_token_by_hash_missing_returns_none(refresh_repo):
    result = await refresh_repo.find_refresh_token_by_hash("nonexistent-hash")
    assert result is None


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_refresh_token_removes_it(user_auth_refresh_repos):
    user_repo, auth_repo, refresh_repo = user_auth_refresh_repos
    user = await _create_user(user_repo)
    created = await refresh_repo.create_refresh_token(_token(user.user_id))

    await refresh_repo.delete_refresh_token(created.refresh_token_id)

    assert await refresh_repo.find_refresh_token_by_hash(created.token_hash) is None


@pytest.mark.asyncio
async def test_delete_refresh_token_missing_is_noop(refresh_repo):
    await refresh_repo.delete_refresh_token(99999)  # must not raise


@pytest.mark.asyncio
async def test_delete_all_for_user_removes_only_that_users_tokens(user_auth_refresh_repos):
    user_repo, auth_repo, refresh_repo = user_auth_refresh_repos
    user1 = await _create_user(user_repo, "one@example.com")
    user2 = await _create_user(user_repo, "two@example.com")

    t1 = await refresh_repo.create_refresh_token(_token(user1.user_id, "u1-a"))
    t2 = await refresh_repo.create_refresh_token(_token(user1.user_id, "u1-b"))
    t3 = await refresh_repo.create_refresh_token(_token(user2.user_id, "u2-a"))

    await refresh_repo.delete_all_for_user(user1.user_id)

    assert await refresh_repo.find_refresh_token_by_hash(t1.token_hash) is None
    assert await refresh_repo.find_refresh_token_by_hash(t2.token_hash) is None
    assert await refresh_repo.find_refresh_token_by_hash(t3.token_hash) is not None


# ---------------------------------------------------------------------------
# CASCADE
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_hard_delete_user_cascades_to_refresh_tokens(user_auth_refresh_repos):
    user_repo, auth_repo, refresh_repo = user_auth_refresh_repos
    user = await _create_user(user_repo)
    token = await refresh_repo.create_refresh_token(_token(user.user_id))

    await user_repo.delete_user(user.user_id, hard_delete=True)

    assert await refresh_repo.find_refresh_token_by_hash(token.token_hash) is None
