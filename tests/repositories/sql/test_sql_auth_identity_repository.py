import uuid

import pytest

from src.fastapi_auth_lib.core.exceptions import DuplicateEntityException
from src.fastapi_auth_lib.models.auth_identity import AuthIdentity
from src.fastapi_auth_lib.models.base import AuthProvider
from src.fastapi_auth_lib.models.user import UserProfile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _create_user(user_repo, email="test@example.com"):
    """Create a user and return it. Needed before creating an identity."""
    return await user_repo.create_user(UserProfile(email=email))


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_auth_identity_assigns_id(both_repos):
    user_repo, identity_repo = both_repos
    user = await _create_user(user_repo)

    identity = AuthIdentity(
        user_id=user.user_id,
        provider=AuthProvider.PASSWORD,
        provider_subject="test@example.com",
        password_hash="hashed_password",
    )
    created = await identity_repo.create_auth_identity(identity)

    assert created.auth_identity_id is not None
    assert created.user_id == user.user_id
    assert created.provider == AuthProvider.PASSWORD
    assert created.provider_subject == "test@example.com"
    assert created.password_hash == "hashed_password"


@pytest.mark.asyncio
async def test_create_duplicate_provider_subject_raises(both_repos):
    user_repo, identity_repo = both_repos
    user1 = await _create_user(user_repo, "dup@example.com")
    user2 = await _create_user(user_repo, "other@example.com")

    await identity_repo.create_auth_identity(
        AuthIdentity(
            user_id=user1.user_id,
            provider=AuthProvider.PASSWORD,
            provider_subject="dup@example.com",
            password_hash="hash1",
        )
    )

    with pytest.raises(DuplicateEntityException):
        await identity_repo.create_auth_identity(
            AuthIdentity(
                user_id=user2.user_id,
                provider=AuthProvider.PASSWORD,
                provider_subject="dup@example.com",  # conflict
                password_hash="hash2",
            )
        )


@pytest.mark.asyncio
async def test_create_duplicate_user_id_raises(both_repos):
    """1:1 constraint: one identity per user."""
    user_repo, identity_repo = both_repos
    user = await _create_user(user_repo)

    await identity_repo.create_auth_identity(
        AuthIdentity(
            user_id=user.user_id,
            provider=AuthProvider.PASSWORD,
            provider_subject="first@example.com",
            password_hash="hash1",
        )
    )

    with pytest.raises(DuplicateEntityException):
        await identity_repo.create_auth_identity(
            AuthIdentity(
                user_id=user.user_id,  # same user, different subject
                provider=AuthProvider.PASSWORD,
                provider_subject="second@example.com",
                password_hash="hash2",
            )
        )


# ---------------------------------------------------------------------------
# FIND BY ID
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_find_auth_identity_by_id_returns_identity(both_repos):
    user_repo, identity_repo = both_repos
    user = await _create_user(user_repo)
    created = await identity_repo.create_auth_identity(
        AuthIdentity(
            user_id=user.user_id,
            provider=AuthProvider.PASSWORD,
            provider_subject="find@example.com",
            password_hash="hash",
        )
    )

    fetched = await identity_repo.find_auth_identity_by_id(created.auth_identity_id)

    assert fetched is not None
    assert fetched.auth_identity_id == created.auth_identity_id
    assert fetched.provider_subject == "find@example.com"


@pytest.mark.asyncio
async def test_find_auth_identity_by_id_missing_returns_none(auth_identity_repo):
    result = await auth_identity_repo.find_auth_identity_by_id(99999)
    assert result is None


# ---------------------------------------------------------------------------
# FIND BY USER ID
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_find_auth_identity_by_user_id_returns_identity(both_repos):
    user_repo, identity_repo = both_repos
    user = await _create_user(user_repo)
    await identity_repo.create_auth_identity(
        AuthIdentity(
            user_id=user.user_id,
            provider=AuthProvider.PASSWORD,
            provider_subject="byuser@example.com",
            password_hash="hash",
        )
    )

    fetched = await identity_repo.find_auth_identity_by_user_id(user.user_id)

    assert fetched is not None
    assert fetched.user_id == user.user_id
    assert fetched.provider_subject == "byuser@example.com"


@pytest.mark.asyncio
async def test_find_auth_identity_by_user_id_missing_returns_none(auth_identity_repo):
    result = await auth_identity_repo.find_auth_identity_by_user_id(uuid.uuid4())
    assert result is None


# ---------------------------------------------------------------------------
# FIND BY PROVIDER SUBJECT
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_find_auth_identity_by_provider_subject_returns_identity(both_repos):
    user_repo, identity_repo = both_repos
    user = await _create_user(user_repo)
    await identity_repo.create_auth_identity(
        AuthIdentity(
            user_id=user.user_id,
            provider=AuthProvider.PASSWORD,
            provider_subject="bysubject@example.com",
            password_hash="hash",
        )
    )

    fetched = await identity_repo.find_auth_identity_by_provider_subject(
        AuthProvider.PASSWORD, "bysubject@example.com"
    )

    assert fetched is not None
    assert fetched.provider_subject == "bysubject@example.com"


@pytest.mark.asyncio
async def test_find_auth_identity_by_provider_subject_missing_returns_none(
    auth_identity_repo,
):
    result = await auth_identity_repo.find_auth_identity_by_provider_subject(
        AuthProvider.PASSWORD, "ghost@example.com"
    )
    assert result is None


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_auth_identity_changes_fields(both_repos):
    user_repo, identity_repo = both_repos
    user = await _create_user(user_repo)
    created = await identity_repo.create_auth_identity(
        AuthIdentity(
            user_id=user.user_id,
            provider=AuthProvider.PASSWORD,
            provider_subject="old@example.com",
            password_hash="old_hash",
        )
    )

    updated_model = AuthIdentity(
        user_id=user.user_id,
        provider=AuthProvider.PASSWORD,
        provider_subject="new@example.com",
        password_hash="new_hash",
    )
    updated = await identity_repo.update_auth_identity(
        created.auth_identity_id, updated_model
    )

    assert updated is not None
    assert updated.provider_subject == "new@example.com"
    assert updated.password_hash == "new_hash"


@pytest.mark.asyncio
async def test_update_missing_identity_returns_none(auth_identity_repo):
    model = AuthIdentity(
        user_id=uuid.uuid4(),
        provider=AuthProvider.PASSWORD,
        provider_subject="nobody@example.com",
        password_hash="hash",
    )
    result = await auth_identity_repo.update_auth_identity(99999, model)
    assert result is None


@pytest.mark.asyncio
async def test_update_subject_conflict_raises(both_repos):
    user_repo, identity_repo = both_repos
    user1 = await _create_user(user_repo, "taken@example.com")
    user2 = await _create_user(user_repo, "free@example.com")

    await identity_repo.create_auth_identity(
        AuthIdentity(
            user_id=user1.user_id,
            provider=AuthProvider.PASSWORD,
            provider_subject="taken@example.com",
            password_hash="hash1",
        )
    )
    created2 = await identity_repo.create_auth_identity(
        AuthIdentity(
            user_id=user2.user_id,
            provider=AuthProvider.PASSWORD,
            provider_subject="free@example.com",
            password_hash="hash2",
        )
    )

    conflict_model = AuthIdentity(
        user_id=user2.user_id,
        provider=AuthProvider.PASSWORD,
        provider_subject="taken@example.com",  # conflict
        password_hash="hash2_updated",
    )

    with pytest.raises(DuplicateEntityException):
        await identity_repo.update_auth_identity(
            created2.auth_identity_id, conflict_model
        )


@pytest.mark.asyncio
async def test_update_user_id_reassignment_conflict_raises(both_repos):
    """Reassigning identity to a user who already has one should fail."""
    user_repo, identity_repo = both_repos
    user1 = await _create_user(user_repo, "user1@example.com")
    user2 = await _create_user(user_repo, "user2@example.com")

    identity1 = await identity_repo.create_auth_identity(
        AuthIdentity(
            user_id=user1.user_id,
            provider=AuthProvider.PASSWORD,
            provider_subject="user1@example.com",
            password_hash="hash1",
        )
    )
    await identity_repo.create_auth_identity(
        AuthIdentity(
            user_id=user2.user_id,
            provider=AuthProvider.PASSWORD,
            provider_subject="user2@example.com",
            password_hash="hash2",
        )
    )

    reassign_model = AuthIdentity(
        user_id=user2.user_id,  # try to move identity1 to user2
        provider=AuthProvider.PASSWORD,
        provider_subject="user1@example.com",
        password_hash="hash1",
    )

    with pytest.raises(DuplicateEntityException):
        await identity_repo.update_auth_identity(identity1.auth_identity_id, reassign_model)


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_auth_identity_removes_it(both_repos):
    user_repo, identity_repo = both_repos
    user = await _create_user(user_repo)
    created = await identity_repo.create_auth_identity(
        AuthIdentity(
            user_id=user.user_id,
            provider=AuthProvider.PASSWORD,
            provider_subject="del@example.com",
            password_hash="hash",
        )
    )

    await identity_repo.delete_auth_identity(created.auth_identity_id)

    fetched = await identity_repo.find_auth_identity_by_id(created.auth_identity_id)
    assert fetched is None


@pytest.mark.asyncio
async def test_delete_missing_identity_is_noop(auth_identity_repo):
    # Should not raise
    await auth_identity_repo.delete_auth_identity(99999)


# ---------------------------------------------------------------------------
# CASCADE DELETE (user deletion removes identity)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_hard_delete_user_cascades_to_identity(both_repos):
    """DB-level CASCADE: deleting a user removes their identity."""
    user_repo, identity_repo = both_repos
    user = await _create_user(user_repo)
    identity = await identity_repo.create_auth_identity(
        AuthIdentity(
            user_id=user.user_id,
            provider=AuthProvider.PASSWORD,
            provider_subject="cascade@example.com",
            password_hash="hash",
        )
    )

    await user_repo.delete_user(user.user_id, hard_delete=True)

    fetched_identity = await identity_repo.find_auth_identity_by_id(
        identity.auth_identity_id
    )
    assert fetched_identity is None
