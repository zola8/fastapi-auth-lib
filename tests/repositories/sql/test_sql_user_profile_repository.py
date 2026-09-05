import uuid

import pytest

from src.fastapi_auth_lib.core.exceptions import DuplicateEntityException
from src.fastapi_auth_lib.models.base import UserRole
from src.fastapi_auth_lib.models.base import UserStatus
from src.fastapi_auth_lib.models.user import UserProfile


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_user_assigns_uuid(user_repo):
    user = UserProfile(email="alice@example.com", username="alice")
    assert user.user_id is None

    created = await user_repo.create_user(user)

    assert created.user_id is not None
    assert created.email == "alice@example.com"
    assert created.username == "alice"
    assert created.status == UserStatus.INACTIVE


@pytest.mark.asyncio
async def test_create_user_respects_provided_uuid(user_repo):
    fixed_id = uuid.uuid4()
    user = UserProfile(user_id=fixed_id, email="bob@example.com")

    created = await user_repo.create_user(user)

    assert created.user_id == fixed_id


@pytest.mark.asyncio
async def test_create_user_stores_roles(user_repo):
    user = UserProfile(
        email="carol@example.com",
        roles=[UserRole.USER, UserRole.ADMIN],
    )

    created = await user_repo.create_user(user)

    assert UserRole.USER in created.roles
    assert UserRole.ADMIN in created.roles


@pytest.mark.asyncio
async def test_create_duplicate_email_raises(user_repo):
    await user_repo.create_user(UserProfile(email="dup@example.com"))

    with pytest.raises(DuplicateEntityException):
        await user_repo.create_user(UserProfile(email="dup@example.com"))


# ---------------------------------------------------------------------------
# FIND BY ID
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_find_user_by_id_returns_user(user_repo):
    created = await user_repo.create_user(UserProfile(email="find@example.com"))

    fetched = await user_repo.find_user_by_id(created.user_id)

    assert fetched is not None
    assert fetched.email == "find@example.com"


@pytest.mark.asyncio
async def test_find_user_by_id_missing_returns_none(user_repo):
    result = await user_repo.find_user_by_id(uuid.uuid4())
    assert result is None


# ---------------------------------------------------------------------------
# FIND BY EMAIL
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_find_user_by_email_returns_user(user_repo):
    await user_repo.create_user(UserProfile(email="lookup@example.com"))

    fetched = await user_repo.find_user_by_email("lookup@example.com")

    assert fetched is not None
    assert fetched.email == "lookup@example.com"


@pytest.mark.asyncio
async def test_find_user_by_email_missing_returns_none(user_repo):
    result = await user_repo.find_user_by_email("ghost@example.com")
    assert result is None


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_user_changes_fields(user_repo):
    created = await user_repo.create_user(
        UserProfile(email="upd@example.com", username="old")
    )

    updated_model = UserProfile(
        email="upd@example.com",
        username="new",
        status=UserStatus.ACTIVE,
        roles=[UserRole.ADMIN],
    )
    updated = await user_repo.update_user(created.user_id, updated_model)

    assert updated is not None
    assert updated.username == "new"
    assert updated.status == UserStatus.ACTIVE
    assert UserRole.ADMIN in updated.roles


@pytest.mark.asyncio
async def test_update_missing_user_returns_none(user_repo):
    model = UserProfile(email="nobody@example.com")
    result = await user_repo.update_user(uuid.uuid4(), model)
    assert result is None


@pytest.mark.asyncio
async def test_update_user_email_conflict_raises(user_repo):
    await user_repo.create_user(UserProfile(email="taken@example.com"))
    target = await user_repo.create_user(UserProfile(email="free@example.com"))

    conflict = UserProfile(email="taken@example.com")

    with pytest.raises(DuplicateEntityException):
        await user_repo.update_user(target.user_id, conflict)


@pytest.mark.asyncio
async def test_update_user_same_email_does_not_raise(user_repo):
    created = await user_repo.create_user(UserProfile(email="same@example.com"))

    same_email = UserProfile(email="same@example.com", username="changed")
    updated = await user_repo.update_user(created.user_id, same_email)

    assert updated is not None
    assert updated.username == "changed"


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_soft_delete_sets_status_deleted(user_repo):
    created = await user_repo.create_user(UserProfile(email="soft@example.com"))

    await user_repo.delete_user(created.user_id, hard_delete=False)

    fetched = await user_repo.find_user_by_id(created.user_id)
    assert fetched is not None
    assert fetched.status == UserStatus.DELETED


@pytest.mark.asyncio
async def test_hard_delete_removes_user(user_repo):
    created = await user_repo.create_user(UserProfile(email="hard@example.com"))

    await user_repo.delete_user(created.user_id, hard_delete=True)

    fetched = await user_repo.find_user_by_id(created.user_id)
    assert fetched is None


@pytest.mark.asyncio
async def test_delete_missing_user_is_noop(user_repo):
    # Should not raise
    await user_repo.delete_user(uuid.uuid4())


# ---------------------------------------------------------------------------
# LIST
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_list_users_returns_all(user_repo):
    await user_repo.create_user(UserProfile(email="a@example.com"))
    await user_repo.create_user(UserProfile(email="b@example.com"))

    users = await user_repo.list_users()

    assert len(users) == 2
    emails = {u.email for u in users}
    assert emails == {"a@example.com", "b@example.com"}


@pytest.mark.asyncio
async def test_list_users_empty(user_repo):
    users = await user_repo.list_users()
    assert users == []
