import uuid

import pytest

from fastapi_auth_lib.core.exceptions import DuplicateEntityException
from fastapi_auth_lib.core.exceptions import EntityNotFoundException
from fastapi_auth_lib.models.auth_identity import AuthIdentity
from fastapi_auth_lib.models.base import AuthProvider


def _create_auth_identity(**kwargs) -> AuthIdentity:
    """Helper to create an AuthIdentity with overridable defaults."""
    defaults = {
        "user_id": uuid.uuid4(),
        "provider": AuthProvider.PASSWORD,
        "provider_subject": "default@example.com",
        "password_hash": "$2b$12$fakehash",
    }
    defaults.update(kwargs)
    return AuthIdentity(**defaults)


# --- Create Tests ---

def test_create_auth_identity_success(sql_sync_identity_repo):
    user_id = uuid.uuid4()
    created = sql_sync_identity_repo.create_auth_identity(
        _create_auth_identity(user_id=user_id, provider_subject="new@example.com")
    )

    assert created.auth_identity_id is not None
    assert isinstance(created.auth_identity_id, int)
    assert created.auth_identity_id > 0
    assert created.user_id == user_id
    assert created.provider == AuthProvider.PASSWORD
    assert created.provider_subject == "new@example.com"
    assert created.created_at is not None
    assert created.updated_at is None


def test_create_generates_sequential_ids(sql_sync_identity_repo):
    i1 = sql_sync_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="seq1@example.com")
    )
    i2 = sql_sync_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="seq2@example.com")
    )
    assert i2.auth_identity_id == i1.auth_identity_id + 1


def test_create_duplicate_provider_subject_raises(sql_sync_identity_repo):
    sql_sync_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="dup@example.com")
    )

    with pytest.raises(DuplicateEntityException) as exc_info:
        sql_sync_identity_repo.create_auth_identity(
            _create_auth_identity(provider_subject="dup@example.com")
        )

    assert exc_info.value.field == "provider_subject"
    assert exc_info.value.value == "dup@example.com"


def test_create_duplicate_user_id_raises(sql_sync_identity_repo):
    shared_user_id = uuid.uuid4()
    sql_sync_identity_repo.create_auth_identity(
        _create_auth_identity(user_id=shared_user_id, provider_subject="sub1@example.com")
    )

    with pytest.raises(DuplicateEntityException) as exc_info:
        sql_sync_identity_repo.create_auth_identity(
            _create_auth_identity(user_id=shared_user_id, provider_subject="sub2@example.com")
        )

    assert exc_info.value.field == "user_id"
    assert str(shared_user_id) in exc_info.value.value


# --- Get Tests ---

def test_get_auth_identity_by_id_success(sql_sync_identity_repo):
    created = sql_sync_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="get_by_id@example.com")
    )
    fetched = sql_sync_identity_repo.get_auth_identity(created.auth_identity_id)

    assert fetched.auth_identity_id == created.auth_identity_id
    assert fetched.provider_subject == "get_by_id@example.com"


def test_get_auth_identity_by_id_not_found_raises(sql_sync_identity_repo):
    with pytest.raises(EntityNotFoundException) as exc_info:
        sql_sync_identity_repo.get_auth_identity(99999)

    assert exc_info.value.field == "auth_identity_id"


def test_get_auth_identity_by_id_invalid_raises(sql_sync_identity_repo):
    with pytest.raises(EntityNotFoundException):
        sql_sync_identity_repo.get_auth_identity(-1)

    with pytest.raises(EntityNotFoundException):
        sql_sync_identity_repo.get_auth_identity(0)

    with pytest.raises(EntityNotFoundException):
        sql_sync_identity_repo.get_auth_identity(True)


def test_get_auth_identity_by_user_id_success(sql_sync_identity_repo):
    user_id = uuid.uuid4()
    created = sql_sync_identity_repo.create_auth_identity(
        _create_auth_identity(user_id=user_id, provider_subject="by_uid@example.com")
    )
    fetched = sql_sync_identity_repo.get_auth_identity_by_user_id(user_id)

    assert fetched.auth_identity_id == created.auth_identity_id
    assert fetched.user_id == user_id


def test_get_auth_identity_by_user_id_not_found_raises(sql_sync_identity_repo):
    fake_user_id = uuid.uuid4()
    with pytest.raises(EntityNotFoundException) as exc_info:
        sql_sync_identity_repo.get_auth_identity_by_user_id(fake_user_id)

    assert exc_info.value.field == "user_id"
    assert str(fake_user_id) in exc_info.value.value


def test_get_auth_identity_by_provider_subject_success(sql_sync_identity_repo):
    created = sql_sync_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="by_prov_sub@example.com")
    )
    fetched = sql_sync_identity_repo.get_auth_identity_by_provider_subject(
        provider=AuthProvider.PASSWORD,
        provider_subject="by_prov_sub@example.com",
    )

    assert fetched.auth_identity_id == created.auth_identity_id
    assert fetched.provider_subject == "by_prov_sub@example.com"


def test_get_auth_identity_by_provider_subject_not_found_raises(sql_sync_identity_repo):
    with pytest.raises(EntityNotFoundException) as exc_info:
        sql_sync_identity_repo.get_auth_identity_by_provider_subject(
            provider=AuthProvider.PASSWORD,
            provider_subject="nonexistent@example.com",
        )

    assert exc_info.value.field == "provider_subject"
    assert exc_info.value.value == "nonexistent@example.com"


# --- Update Tests ---

def test_update_mutable_fields(sql_sync_identity_repo):
    created = sql_sync_identity_repo.create_auth_identity(
        _create_auth_identity(
            provider_subject="old_sub@example.com",
            password_hash="$old_hash",
        )
    )

    update_identity = _create_auth_identity(
        user_id=uuid.uuid4(),  # immutable - ignored
        provider=AuthProvider.PASSWORD,  # immutable - ignored
        provider_subject="new_sub@example.com",
        password_hash="$new_hash",
    )

    updated = sql_sync_identity_repo.update_auth_identity(
        created.auth_identity_id, update_identity
    )

    # Mutable fields changed
    assert updated.provider_subject == "new_sub@example.com"
    assert updated.password_hash == "$new_hash"
    assert updated.updated_at is not None

    # Immutable fields preserved
    assert updated.auth_identity_id == created.auth_identity_id
    assert updated.user_id == created.user_id
    assert updated.provider == created.provider
    # assert updated.created_at == created.created_at
    # TODO create timezone decorator?


def test_update_reindexes_provider_subject(sql_sync_identity_repo):
    created = sql_sync_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="old_idx@example.com")
    )

    update_identity = _create_auth_identity(provider_subject="new_idx@example.com")
    sql_sync_identity_repo.update_auth_identity(
        created.auth_identity_id, update_identity
    )

    # Old key no longer resolves
    with pytest.raises(EntityNotFoundException):
        sql_sync_identity_repo.get_auth_identity_by_provider_subject(
            provider=AuthProvider.PASSWORD,
            provider_subject="old_idx@example.com",
        )

    # New key resolves correctly
    fetched = sql_sync_identity_repo.get_auth_identity_by_provider_subject(
        provider=AuthProvider.PASSWORD,
        provider_subject="new_idx@example.com",
    )
    assert fetched.auth_identity_id == created.auth_identity_id


def test_update_to_existing_provider_subject_raises(sql_sync_identity_repo):
    sql_sync_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="taken@example.com")
    )
    target = sql_sync_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="target@example.com")
    )

    update_identity = _create_auth_identity(provider_subject="taken@example.com")

    with pytest.raises(DuplicateEntityException) as exc_info:
        sql_sync_identity_repo.update_auth_identity(
            target.auth_identity_id, update_identity
        )

    assert exc_info.value.field == "provider_subject"
    assert exc_info.value.value == "taken@example.com"


def test_update_same_provider_subject_succeeds(sql_sync_identity_repo):
    """Updating with the same provider_subject should not raise duplicate."""
    created = sql_sync_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="same@example.com", password_hash="$old")
    )

    update_identity = _create_auth_identity(
        provider_subject="same@example.com", password_hash="$new"
    )
    updated = sql_sync_identity_repo.update_auth_identity(
        created.auth_identity_id, update_identity
    )

    assert updated.password_hash == "$new"
    assert updated.provider_subject == "same@example.com"


def test_update_nonexistent_raises(sql_sync_identity_repo):
    with pytest.raises(EntityNotFoundException):
        sql_sync_identity_repo.update_auth_identity(
            99999, _create_auth_identity()
        )


# --- Delete Tests ---

def test_delete_removes_identity(sql_sync_identity_repo):
    created = sql_sync_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="to_delete@example.com")
    )
    sql_sync_identity_repo.delete_auth_identity(created.auth_identity_id)

    with pytest.raises(EntityNotFoundException):
        sql_sync_identity_repo.get_auth_identity(created.auth_identity_id)


def test_delete_clears_all_indexes(sql_sync_identity_repo):
    user_id = uuid.uuid4()
    created = sql_sync_identity_repo.create_auth_identity(
        _create_auth_identity(user_id=user_id, provider_subject="del_idx@example.com")
    )
    sql_sync_identity_repo.delete_auth_identity(created.auth_identity_id)

    with pytest.raises(EntityNotFoundException):
        sql_sync_identity_repo.get_auth_identity_by_user_id(user_id)

    with pytest.raises(EntityNotFoundException):
        sql_sync_identity_repo.get_auth_identity_by_provider_subject(
            provider=AuthProvider.PASSWORD,
            provider_subject="del_idx@example.com",
        )


def test_delete_nonexistent_raises(sql_sync_identity_repo):
    with pytest.raises(EntityNotFoundException):
        sql_sync_identity_repo.delete_auth_identity(99999)


def test_delete_then_recreate_same_provider_subject(sql_sync_identity_repo):
    """After delete, provider_subject index should be cleared allowing reuse."""
    original = sql_sync_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="reuse@example.com")
    )
    sql_sync_identity_repo.delete_auth_identity(original.auth_identity_id)

    recreated = sql_sync_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="reuse@example.com")
    )

    assert recreated.provider_subject == "reuse@example.com"
    assert recreated.created_at != original.created_at
    assert recreated.updated_at is None

    fetched = sql_sync_identity_repo.get_auth_identity(recreated.auth_identity_id)
    assert fetched.provider_subject == "reuse@example.com"


def test_delete_then_recreate_same_user_id(sql_sync_identity_repo):
    """After delete, user_id index should be cleared allowing reuse."""
    user_id = uuid.uuid4()
    original = sql_sync_identity_repo.create_auth_identity(
        _create_auth_identity(user_id=user_id, provider_subject="reuse_uid@example.com")
    )
    sql_sync_identity_repo.delete_auth_identity(original.auth_identity_id)

    recreated = sql_sync_identity_repo.create_auth_identity(
        _create_auth_identity(user_id=user_id, provider_subject="reuse_uid2@example.com")
    )

    # Functionally distinct identity for the same user
    assert recreated.user_id == user_id
    assert recreated.provider_subject == "reuse_uid2@example.com"
    assert recreated.created_at != original.created_at
