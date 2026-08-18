import uuid

import pytest

from fastapi_auth_lib.core.exceptions import DuplicateEntityException
from fastapi_auth_lib.core.exceptions import EntityNotFoundException
from fastapi_auth_lib.models.base import UserRole
from fastapi_auth_lib.models.base import UserStatus
from fastapi_auth_lib.models.user import UserProfile


def _create_profile(**kwargs) -> UserProfile:
    """Helper to create a UserProfile with defaults that can be overridden."""
    defaults = {
        "email": "default@example.com",
        "username": "default_user",
        "roles": [UserRole.USER],
        "status": UserStatus.ACTIVE,
    }
    defaults.update(kwargs)
    return UserProfile(**defaults)


# --- Create User Tests ---

@pytest.mark.asyncio
async def test_create_user_success(in_memory_user_repo):
    user_in = _create_profile(email="new@example.com")
    created = await in_memory_user_repo.create_user(user_in)

    assert created.user_id is not None
    assert created.email == "new@example.com"
    assert created.status == UserStatus.ACTIVE
    assert created.created_at is not None
    assert created.updated_at is None
    # Ensure returned object is a deep copy
    assert created is not user_in


@pytest.mark.asyncio
async def test_create_user_generates_unique_ids(in_memory_user_repo):
    u1 = await in_memory_user_repo.create_user(_create_profile(email="u1@example.com"))
    u2 = await in_memory_user_repo.create_user(_create_profile(email="u2@example.com"))
    assert u1.user_id != u2.user_id


@pytest.mark.asyncio
async def test_create_user_duplicate_email_raises(in_memory_user_repo):
    await in_memory_user_repo.create_user(_create_profile(email="dup@example.com"))

    with pytest.raises(DuplicateEntityException) as exc_info:
        await in_memory_user_repo.create_user(_create_profile(email="dup@example.com"))

    assert exc_info.value.field == "email"
    assert exc_info.value.value == "dup@example.com"


# --- Get User Tests ---

@pytest.mark.asyncio
async def test_get_user_by_id_success(in_memory_user_repo):
    created = await in_memory_user_repo.create_user(_create_profile(email="get_id@example.com"))
    fetched = await in_memory_user_repo.get_user_by_id(created.user_id)

    assert fetched.user_id == created.user_id
    assert fetched.email == created.email
    assert fetched is not created


@pytest.mark.asyncio
async def test_get_user_by_id_not_found_raises(in_memory_user_repo):
    fake_id = uuid.uuid4()
    with pytest.raises(EntityNotFoundException) as exc_info:
        await in_memory_user_repo.get_user_by_id(fake_id)

    assert exc_info.value.field == "user_id"
    assert str(fake_id) in exc_info.value.value


@pytest.mark.asyncio
async def test_get_user_by_email_success(in_memory_user_repo):
    created = await in_memory_user_repo.create_user(_create_profile(email="get_email@example.com"))
    fetched = await in_memory_user_repo.get_user_by_email("get_email@example.com")

    assert fetched.user_id == created.user_id
    assert fetched.email == "get_email@example.com"


@pytest.mark.asyncio
async def test_get_user_by_email_not_found_raises(in_memory_user_repo):
    with pytest.raises(EntityNotFoundException) as exc_info:
        await in_memory_user_repo.get_user_by_email("nonexistent@example.com")

    assert exc_info.value.field == "email"
    assert exc_info.value.value == "nonexistent@example.com"


# --- Update User Tests ---

@pytest.mark.asyncio
async def test_update_user_mutable_fields(in_memory_user_repo):
    created = await in_memory_user_repo.create_user(_create_profile(
        email="update@example.com",
        username="old_name",
        roles=[UserRole.USER],
        status=UserStatus.ACTIVE,
    ))

    update_profile = _create_profile(
        email="should_be_ignored@example.com",
        username="new_name",
        roles=[UserRole.ADMIN],
        status=UserStatus.INACTIVE,
    )

    updated = await in_memory_user_repo.update_user(created.user_id, update_profile)

    # Mutable fields changed
    assert updated.username == "new_name"
    assert updated.roles == [UserRole.ADMIN]
    assert updated.status == UserStatus.INACTIVE
    assert updated.updated_at is not None
    assert updated.updated_at > created.created_at

    # Immutable fields preserved
    assert updated.user_id == created.user_id
    assert updated.email == "update@example.com"
    assert updated.created_at == created.created_at


@pytest.mark.asyncio
async def test_update_user_not_found_raises(in_memory_user_repo):
    fake_id = uuid.uuid4()
    profile = _create_profile()

    with pytest.raises(EntityNotFoundException):
        await in_memory_user_repo.update_user(fake_id, profile)


@pytest.mark.asyncio
async def test_update_deleted_user_raises(in_memory_user_repo):
    created = await in_memory_user_repo.create_user(_create_profile(email="del_update@example.com"))
    await in_memory_user_repo.delete_user(created.user_id, hard_delete=False)

    with pytest.raises(EntityNotFoundException):
        await in_memory_user_repo.update_user(created.user_id, _create_profile(username="ghost"))


# --- Delete User Tests ---

@pytest.mark.asyncio
async def test_soft_delete_sets_status(in_memory_user_repo):
    created = await in_memory_user_repo.create_user(_create_profile(email="soft_del@example.com"))
    await in_memory_user_repo.delete_user(created.user_id, hard_delete=False)

    # User still exists but status is DELETED
    user = await in_memory_user_repo.get_user_by_id(created.user_id)
    assert user.status == UserStatus.DELETED
    assert user.updated_at is not None


@pytest.mark.asyncio
async def test_soft_delete_already_deleted_is_idempotent(in_memory_user_repo):
    created = await in_memory_user_repo.create_user(_create_profile(email="idempotent@example.com"))
    await in_memory_user_repo.delete_user(created.user_id, hard_delete=False)

    first_updated_at = (await in_memory_user_repo.get_user_by_id(created.user_id)).updated_at

    # Second soft delete should not change anything
    await in_memory_user_repo.delete_user(created.user_id, hard_delete=False)
    user = await in_memory_user_repo.get_user_by_id(created.user_id)

    assert user.status == UserStatus.DELETED
    assert user.updated_at == first_updated_at


@pytest.mark.asyncio
async def test_hard_delete_removes_user(in_memory_user_repo):
    created = await in_memory_user_repo.create_user(_create_profile(email="hard_del@example.com"))
    await in_memory_user_repo.delete_user(created.user_id, hard_delete=True)

    with pytest.raises(EntityNotFoundException):
        await in_memory_user_repo.get_user_by_id(created.user_id)

    with pytest.raises(EntityNotFoundException):
        await in_memory_user_repo.get_user_by_email("hard_del@example.com")


@pytest.mark.asyncio
async def test_delete_nonexistent_user_raises(in_memory_user_repo):
    fake_id = uuid.uuid4()
    with pytest.raises(EntityNotFoundException):
        await in_memory_user_repo.delete_user(fake_id)


@pytest.mark.asyncio
async def test_hard_delete_then_recreate_same_email(in_memory_user_repo):
    original = await in_memory_user_repo.create_user(_create_profile(email="reuse@example.com"))
    await in_memory_user_repo.delete_user(original.user_id, hard_delete=True)

    recreated = await in_memory_user_repo.create_user(_create_profile(email="reuse@example.com"))
    assert recreated.user_id != original.user_id
    assert recreated.email == "reuse@example.com"


# --- Isolation / Deep Copy Tests ---

@pytest.mark.asyncio
async def test_returned_user_is_deep_copy(in_memory_user_repo):
    """Modifying returned objects should not affect repository state."""
    created = await in_memory_user_repo.create_user(_create_profile(email="copy_test@example.com"))

    fetched = await in_memory_user_repo.get_user_by_id(created.user_id)
    fetched.username = "hacked"
    fetched.roles.append(UserRole.ADMIN)

    refetched = await in_memory_user_repo.get_user_by_id(created.user_id)
    assert refetched.username != "hacked"
    assert UserRole.ADMIN not in refetched.roles


# --- get_all_users Tests ---

@pytest.mark.asyncio
async def test_get_all_users_empty_repo(in_memory_user_repo):
    result = await in_memory_user_repo.get_all_users()
    assert result == []
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_get_all_users_returns_all_created(in_memory_user_repo):
    """Returns all created users."""
    u1 = await in_memory_user_repo.create_user(
        _create_profile(email="all1@example.com", username="user1")
    )
    u2 = await in_memory_user_repo.create_user(
        _create_profile(email="all2@example.com", username="user2")
    )
    u3 = await in_memory_user_repo.create_user(
        _create_profile(email="all3@example.com", username="user3")
    )

    result = await in_memory_user_repo.get_all_users()

    assert len(result) == 3
    returned_ids = {u.user_id for u in result}
    assert returned_ids == {u1.user_id, u2.user_id, u3.user_id}


@pytest.mark.asyncio
async def test_get_all_users_includes_soft_deleted(in_memory_user_repo):
    """Soft-deleted users are included in results."""
    active = await in_memory_user_repo.create_user(
        _create_profile(email="active_all@example.com")
    )
    deleted = await in_memory_user_repo.create_user(
        _create_profile(email="deleted_all@example.com")
    )
    await in_memory_user_repo.delete_user(deleted.user_id, hard_delete=False)

    result = await in_memory_user_repo.get_all_users()

    assert len(result) == 2
    returned_ids = {u.user_id for u in result}
    assert active.user_id in returned_ids
    assert deleted.user_id in returned_ids

    deleted_in_result = next(u for u in result if u.user_id == deleted.user_id)
    assert deleted_in_result.status == UserStatus.DELETED


@pytest.mark.asyncio
async def test_get_all_users_excludes_hard_deleted(in_memory_user_repo):
    """Hard-deleted users are NOT included in results."""
    kept = await in_memory_user_repo.create_user(
        _create_profile(email="kept_all@example.com")
    )
    removed = await in_memory_user_repo.create_user(
        _create_profile(email="removed_all@example.com")
    )
    await in_memory_user_repo.delete_user(removed.user_id, hard_delete=True)

    result = await in_memory_user_repo.get_all_users()

    assert len(result) == 1
    assert result[0].user_id == kept.user_id


@pytest.mark.asyncio
async def test_get_all_users_returns_deep_copies(in_memory_user_repo):
    """Returned users are deep copies; mutation does not affect repo state."""
    await in_memory_user_repo.create_user(
        _create_profile(email="copy_all@example.com", username="original")
    )

    result = await in_memory_user_repo.get_all_users()
    result[0].username = "mutated"
    result[0].roles.append(UserRole.ADMIN)

    refetched = await in_memory_user_repo.get_all_users()
    assert refetched[0].username == "original"
    assert UserRole.ADMIN not in refetched[0].roles


@pytest.mark.asyncio
async def test_get_all_users_reflects_updates(in_memory_user_repo):
    """Updated users appear with their latest state."""
    created = await in_memory_user_repo.create_user(
        _create_profile(email="updated_all@example.com", username="before")
    )

    update_profile = _create_profile(username="after", roles=[UserRole.ADMIN])
    await in_memory_user_repo.update_user(created.user_id, update_profile)

    result = await in_memory_user_repo.get_all_users()

    assert len(result) == 1
    assert result[0].username == "after"
    assert result[0].roles == [UserRole.ADMIN]
    assert result[0].updated_at is not None
