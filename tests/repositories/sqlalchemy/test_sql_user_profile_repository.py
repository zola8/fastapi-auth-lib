import uuid

import pytest

from fastapi_auth_lib.core.exceptions import DuplicateEntityException
from fastapi_auth_lib.core.exceptions import EntityNotFoundException
from fastapi_auth_lib.models.base import UserRole
from fastapi_auth_lib.models.base import UserStatus
from fastapi_auth_lib.models.user import UserProfile


def _create_profile(**kwargs) -> UserProfile:
    """Helper to create a UserProfile with overridable defaults."""
    defaults = {
        "email": "default@example.com",
        "username": "default_user",
        "roles": [UserRole.USER],
        "status": UserStatus.ACTIVE,
    }
    defaults.update(kwargs)
    return UserProfile(**defaults)


# --- Create Tests ---

def test_create_user_success(sql_sync_user_repo):
    created = sql_sync_user_repo.create_user(
        _create_profile(email="new@example.com")
    )

    assert created.user_id is not None
    assert created.email == "new@example.com"
    assert created.status == UserStatus.ACTIVE
    assert created.created_at is not None
    assert created.updated_at is None


def test_create_user_generates_unique_ids(sql_sync_user_repo):
    u1 = sql_sync_user_repo.create_user(_create_profile(email="u1@example.com"))
    u2 = sql_sync_user_repo.create_user(_create_profile(email="u2@example.com"))
    assert u1.user_id != u2.user_id


def test_create_user_duplicate_email_raises(sql_sync_user_repo):
    sql_sync_user_repo.create_user(_create_profile(email="dup@example.com"))

    with pytest.raises(DuplicateEntityException) as exc_info:
        sql_sync_user_repo.create_user(_create_profile(email="dup@example.com"))

    assert exc_info.value.field == "email"
    assert exc_info.value.value == "dup@example.com"


# --- Get Tests ---

def test_get_user_by_id_success(sql_sync_user_repo):
    created = sql_sync_user_repo.create_user(_create_profile(email="get_id@example.com"))
    fetched = sql_sync_user_repo.get_user_by_id(created.user_id)

    assert fetched.user_id == created.user_id
    assert fetched.email == created.email


def test_get_user_by_id_not_found_raises(sql_sync_user_repo):
    with pytest.raises(EntityNotFoundException) as exc_info:
        sql_sync_user_repo.get_user_by_id(uuid.uuid4())

    assert exc_info.value.field == "user_id"


def test_get_user_by_email_success(sql_sync_user_repo):
    created = sql_sync_user_repo.create_user(_create_profile(email="get_email@example.com"))
    fetched = sql_sync_user_repo.get_user_by_email("get_email@example.com")

    assert fetched.user_id == created.user_id
    assert fetched.email == "get_email@example.com"


def test_get_user_by_email_not_found_raises(sql_sync_user_repo):
    with pytest.raises(EntityNotFoundException) as exc_info:
        sql_sync_user_repo.get_user_by_email("nonexistent@example.com")

    assert exc_info.value.field == "email"
    assert exc_info.value.value == "nonexistent@example.com"


# --- Update Tests ---

def test_update_user_mutable_fields(sql_sync_user_repo):
    created = sql_sync_user_repo.create_user(_create_profile(
        email="update@example.com",
        username="old_name",
        roles=[UserRole.USER],
        status=UserStatus.ACTIVE,
    ))

    update_profile = _create_profile(
        email="should_be_ignored@example.com",  # immutable
        username="new_name",
        roles=[UserRole.ADMIN],
        status=UserStatus.INACTIVE,
    )

    updated = sql_sync_user_repo.update_user(created.user_id, update_profile)

    # Mutable fields changed
    assert updated.username == "new_name"
    assert updated.roles == [UserRole.ADMIN]
    assert updated.status == UserStatus.INACTIVE
    assert updated.updated_at is not None

    # Immutable fields preserved
    assert updated.user_id == created.user_id
    assert updated.email == "update@example.com"
    assert updated.created_at.replace(tzinfo=None) == created.created_at.replace(tzinfo=None)


def test_update_user_not_found_raises(sql_sync_user_repo):
    with pytest.raises(EntityNotFoundException):
        sql_sync_user_repo.update_user(uuid.uuid4(), _create_profile())


def test_update_deleted_user_raises(sql_sync_user_repo):
    created = sql_sync_user_repo.create_user(_create_profile(email="del_update@example.com"))
    sql_sync_user_repo.delete_user(created.user_id, hard_delete=False)

    with pytest.raises(EntityNotFoundException):
        sql_sync_user_repo.update_user(created.user_id, _create_profile(username="ghost"))


# --- Delete Tests ---

def test_soft_delete_sets_status(sql_sync_user_repo):
    created = sql_sync_user_repo.create_user(_create_profile(email="soft_del@example.com"))
    sql_sync_user_repo.delete_user(created.user_id, hard_delete=False)

    user = sql_sync_user_repo.get_user_by_id(created.user_id)
    assert user.status == UserStatus.DELETED
    assert user.updated_at is not None


def test_soft_delete_is_idempotent(sql_sync_user_repo):
    created = sql_sync_user_repo.create_user(_create_profile(email="idempotent@example.com"))
    sql_sync_user_repo.delete_user(created.user_id, hard_delete=False)
    first_updated_at = sql_sync_user_repo.get_user_by_id(created.user_id).updated_at

    sql_sync_user_repo.delete_user(created.user_id, hard_delete=False)
    user = sql_sync_user_repo.get_user_by_id(created.user_id)

    assert user.status == UserStatus.DELETED
    assert user.updated_at == first_updated_at


def test_hard_delete_removes_user(sql_sync_user_repo):
    created = sql_sync_user_repo.create_user(_create_profile(email="hard_del@example.com"))
    sql_sync_user_repo.delete_user(created.user_id, hard_delete=True)

    with pytest.raises(EntityNotFoundException):
        sql_sync_user_repo.get_user_by_id(created.user_id)

    with pytest.raises(EntityNotFoundException):
        sql_sync_user_repo.get_user_by_email("hard_del@example.com")


def test_delete_nonexistent_user_raises(sql_sync_user_repo):
    with pytest.raises(EntityNotFoundException):
        sql_sync_user_repo.delete_user(uuid.uuid4())


# --- get_all_users Tests ---

def test_get_all_users_empty_repo(sql_sync_user_repo):
    result = sql_sync_user_repo.get_all_users()
    assert result == []
    assert isinstance(result, list)


def test_get_all_users_returns_all_created(sql_sync_user_repo):
    u1 = sql_sync_user_repo.create_user(_create_profile(email="all1@example.com"))
    u2 = sql_sync_user_repo.create_user(_create_profile(email="all2@example.com"))

    result = sql_sync_user_repo.get_all_users()

    assert len(result) == 2
    assert {u.user_id for u in result} == {u1.user_id, u2.user_id}


def test_get_all_users_includes_soft_deleted(sql_sync_user_repo):
    sql_sync_user_repo.create_user(_create_profile(email="active@example.com"))
    deleted = sql_sync_user_repo.create_user(_create_profile(email="deleted@example.com"))
    sql_sync_user_repo.delete_user(deleted.user_id, hard_delete=False)

    result = sql_sync_user_repo.get_all_users()

    assert len(result) == 2
    deleted_in_result = next(u for u in result if u.user_id == deleted.user_id)
    assert deleted_in_result.status == UserStatus.DELETED


def test_get_all_users_excludes_hard_deleted(sql_sync_user_repo):
    kept = sql_sync_user_repo.create_user(_create_profile(email="kept@example.com"))
    removed = sql_sync_user_repo.create_user(_create_profile(email="removed@example.com"))
    sql_sync_user_repo.delete_user(removed.user_id, hard_delete=True)

    result = sql_sync_user_repo.get_all_users()

    assert len(result) == 1
    assert result[0].user_id == kept.user_id
