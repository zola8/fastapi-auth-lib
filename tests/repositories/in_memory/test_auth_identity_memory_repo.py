import uuid

import pytest

from fastapi_auth_lib.core.exceptions import DuplicateEntityException
from fastapi_auth_lib.core.exceptions import EntityNotFoundException
from fastapi_auth_lib.models.auth_identity import AuthIdentity
from fastapi_auth_lib.models.base import AuthProvider


def _create_auth_identity(**kwargs) -> AuthIdentity:
    """Helper to create an AuthIdentity with defaults that can be overridden."""
    defaults = {
        "user_id": uuid.uuid4(),
        "provider": AuthProvider.PASSWORD,
        "provider_subject": "default_subject",
        "password_hash": "fake_hash",
    }
    defaults.update(kwargs)
    return AuthIdentity(**defaults)


# --- Create Tests ---

@pytest.mark.asyncio
async def test_create_auth_identity_success(in_memory_auth_identity_repo):
    user_id = uuid.uuid4()
    identity_in = _create_auth_identity(user_id=user_id, provider_subject="new_sub")
    created = await in_memory_auth_identity_repo.create_auth_identity(identity_in)

    assert created.auth_identity_id is not None
    assert isinstance(created.auth_identity_id, int)
    assert created.auth_identity_id > 0
    assert created.user_id == user_id
    assert created.provider == AuthProvider.PASSWORD
    assert created.provider_subject == "new_sub"
    assert created.created_at is not None
    assert created.updated_at is None
    assert created is not identity_in


@pytest.mark.asyncio
async def test_create_generates_sequential_ids(in_memory_auth_identity_repo):
    i1 = await in_memory_auth_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="seq1")
    )
    i2 = await in_memory_auth_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="seq2")
    )
    assert i2.auth_identity_id == i1.auth_identity_id + 1


@pytest.mark.asyncio
async def test_create_duplicate_provider_subject_raises(in_memory_auth_identity_repo):
    await in_memory_auth_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="dup_sub")
    )

    with pytest.raises(DuplicateEntityException) as exc_info:
        await in_memory_auth_identity_repo.create_auth_identity(
            _create_auth_identity(provider_subject="dup_sub")
        )

    assert exc_info.value.field == "provider_subject"
    assert exc_info.value.value == "dup_sub"


@pytest.mark.asyncio
async def test_create_duplicate_user_id_raises(in_memory_auth_identity_repo):
    shared_user_id = uuid.uuid4()
    await in_memory_auth_identity_repo.create_auth_identity(
        _create_auth_identity(user_id=shared_user_id, provider_subject="sub1")
    )

    with pytest.raises(DuplicateEntityException) as exc_info:
        await in_memory_auth_identity_repo.create_auth_identity(
            _create_auth_identity(user_id=shared_user_id, provider_subject="sub2")
        )

    assert exc_info.value.field == "user_id"
    assert str(shared_user_id) in exc_info.value.value


# --- Get Tests ---

@pytest.mark.asyncio
async def test_get_auth_identity_by_id_success(in_memory_auth_identity_repo):
    created = await in_memory_auth_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="get_by_id")
    )
    fetched = await in_memory_auth_identity_repo.get_auth_identity(created.auth_identity_id)

    assert fetched.auth_identity_id == created.auth_identity_id
    assert fetched.provider_subject == "get_by_id"
    assert fetched is not created


@pytest.mark.asyncio
async def test_get_auth_identity_by_id_not_found_raises(in_memory_auth_identity_repo):
    with pytest.raises(EntityNotFoundException) as exc_info:
        await in_memory_auth_identity_repo.get_auth_identity(99999)

    assert exc_info.value.field == "auth_identity_id"


@pytest.mark.asyncio
async def test_get_auth_identity_by_id_invalid_type_raises(in_memory_auth_identity_repo):
    with pytest.raises(EntityNotFoundException):
        await in_memory_auth_identity_repo.get_auth_identity(-1)

    with pytest.raises(EntityNotFoundException):
        await in_memory_auth_identity_repo.get_auth_identity(0)


@pytest.mark.asyncio
async def test_get_auth_identity_by_user_id_success(in_memory_auth_identity_repo):
    user_id = uuid.uuid4()
    created = await in_memory_auth_identity_repo.create_auth_identity(
        _create_auth_identity(user_id=user_id, provider_subject="by_uid")
    )
    fetched = await in_memory_auth_identity_repo.get_auth_identity_by_user_id(user_id)

    assert fetched.auth_identity_id == created.auth_identity_id
    assert fetched.user_id == user_id


@pytest.mark.asyncio
async def test_get_auth_identity_by_user_id_not_found_raises(in_memory_auth_identity_repo):
    fake_user_id = uuid.uuid4()
    with pytest.raises(EntityNotFoundException) as exc_info:
        await in_memory_auth_identity_repo.get_auth_identity_by_user_id(fake_user_id)

    assert exc_info.value.field == "user_id"
    assert str(fake_user_id) in exc_info.value.value


@pytest.mark.asyncio
async def test_get_auth_identity_by_provider_subject_success(in_memory_auth_identity_repo):
    created = await in_memory_auth_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="by_prov_sub")
    )
    fetched = await in_memory_auth_identity_repo.get_auth_identity_by_provider_subject(
        provider=AuthProvider.PASSWORD,
        provider_subject="by_prov_sub",
    )

    assert fetched.auth_identity_id == created.auth_identity_id
    assert fetched.provider_subject == "by_prov_sub"


@pytest.mark.asyncio
async def test_get_auth_identity_by_provider_subject_not_found_raises(in_memory_auth_identity_repo):
    with pytest.raises(EntityNotFoundException) as exc_info:
        await in_memory_auth_identity_repo.get_auth_identity_by_provider_subject(
            provider=AuthProvider.PASSWORD,
            provider_subject="nonexistent",
        )

    assert exc_info.value.field == "provider_subject"
    assert exc_info.value.value == "nonexistent"


# --- Update Tests ---

@pytest.mark.asyncio
async def test_update_mutable_fields(in_memory_auth_identity_repo):
    created = await in_memory_auth_identity_repo.create_auth_identity(
        _create_auth_identity(
            provider_subject="old_sub",
            password_hash="$old_hash",
        )
    )

    update_identity = _create_auth_identity(
        user_id=uuid.uuid4(),
        provider=AuthProvider.PASSWORD,
        provider_subject="new_sub",
        password_hash="$new_hash",
    )

    updated = await in_memory_auth_identity_repo.update_auth_identity(
        created.auth_identity_id, update_identity
    )

    # Mutable fields changed
    assert updated.provider_subject == "new_sub"
    assert updated.password_hash == "$new_hash"
    assert updated.updated_at is not None
    assert updated.updated_at > created.created_at

    # Immutable fields preserved
    assert updated.auth_identity_id == created.auth_identity_id
    assert updated.user_id == created.user_id
    assert updated.provider == created.provider
    assert updated.created_at == created.created_at


@pytest.mark.asyncio
async def test_update_reindexes_provider_subject(in_memory_auth_identity_repo):
    created = await in_memory_auth_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="old_idx")
    )

    update_identity = _create_auth_identity(provider_subject="new_idx")
    await in_memory_auth_identity_repo.update_auth_identity(
        created.auth_identity_id, update_identity
    )

    # Old key no longer resolves
    with pytest.raises(EntityNotFoundException):
        await in_memory_auth_identity_repo.get_auth_identity_by_provider_subject(
            provider=AuthProvider.PASSWORD,
            provider_subject="old_idx",
        )

    # New key resolves correctly
    fetched = await in_memory_auth_identity_repo.get_auth_identity_by_provider_subject(
        provider=AuthProvider.PASSWORD,
        provider_subject="new_idx",
    )
    assert fetched.auth_identity_id == created.auth_identity_id


@pytest.mark.asyncio
async def test_update_to_existing_provider_subject_raises(in_memory_auth_identity_repo):
    await in_memory_auth_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="taken_sub")
    )
    target = await in_memory_auth_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="target_sub")
    )

    update_identity = _create_auth_identity(provider_subject="taken_sub")

    with pytest.raises(DuplicateEntityException) as exc_info:
        await in_memory_auth_identity_repo.update_auth_identity(
            target.auth_identity_id, update_identity
        )

    assert exc_info.value.field == "provider_subject"
    assert exc_info.value.value == "taken_sub"


@pytest.mark.asyncio
async def test_update_same_provider_subject_succeeds(in_memory_auth_identity_repo):
    """Updating with the same provider_subject should not raise duplicate."""
    created = await in_memory_auth_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="same_sub", password_hash="$old")
    )

    update_identity = _create_auth_identity(provider_subject="same_sub", password_hash="$new")
    updated = await in_memory_auth_identity_repo.update_auth_identity(
        created.auth_identity_id, update_identity
    )

    assert updated.password_hash == "$new"
    assert updated.provider_subject == "same_sub"


@pytest.mark.asyncio
async def test_update_nonexistent_raises(in_memory_auth_identity_repo):
    with pytest.raises(EntityNotFoundException):
        await in_memory_auth_identity_repo.update_auth_identity(
            99999, _create_auth_identity()
        )


# --- Delete Tests ---

@pytest.mark.asyncio
async def test_delete_removes_identity(in_memory_auth_identity_repo):
    created = await in_memory_auth_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="to_delete")
    )
    await in_memory_auth_identity_repo.delete_auth_identity(created.auth_identity_id)

    with pytest.raises(EntityNotFoundException):
        await in_memory_auth_identity_repo.get_auth_identity(created.auth_identity_id)


@pytest.mark.asyncio
async def test_delete_clears_all_indexes(in_memory_auth_identity_repo):
    user_id = uuid.uuid4()
    created = await in_memory_auth_identity_repo.create_auth_identity(
        _create_auth_identity(user_id=user_id, provider_subject="del_idx")
    )
    await in_memory_auth_identity_repo.delete_auth_identity(created.auth_identity_id)

    with pytest.raises(EntityNotFoundException):
        await in_memory_auth_identity_repo.get_auth_identity_by_user_id(user_id)

    with pytest.raises(EntityNotFoundException):
        await in_memory_auth_identity_repo.get_auth_identity_by_provider_subject(
            provider=AuthProvider.PASSWORD,
            provider_subject="del_idx",
        )


@pytest.mark.asyncio
async def test_delete_nonexistent_raises(in_memory_auth_identity_repo):
    with pytest.raises(EntityNotFoundException):
        await in_memory_auth_identity_repo.delete_auth_identity(99999)


@pytest.mark.asyncio
async def test_delete_then_recreate_same_provider_subject(in_memory_auth_identity_repo):
    """After delete, provider_subject index should be cleared allowing reuse."""
    original = await in_memory_auth_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="reuse_sub")
    )
    await in_memory_auth_identity_repo.delete_auth_identity(original.auth_identity_id)

    recreated = await in_memory_auth_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="reuse_sub")
    )
    assert recreated.auth_identity_id != original.auth_identity_id
    assert recreated.provider_subject == "reuse_sub"


@pytest.mark.asyncio
async def test_delete_then_recreate_same_user_id(in_memory_auth_identity_repo):
    """After delete, user_id index should be cleared allowing reuse."""
    user_id = uuid.uuid4()
    original = await in_memory_auth_identity_repo.create_auth_identity(
        _create_auth_identity(user_id=user_id, provider_subject="reuse_uid_sub")
    )
    await in_memory_auth_identity_repo.delete_auth_identity(original.auth_identity_id)

    recreated = await in_memory_auth_identity_repo.create_auth_identity(
        _create_auth_identity(user_id=user_id, provider_subject="reuse_uid_sub2")
    )
    assert recreated.auth_identity_id != original.auth_identity_id
    assert recreated.user_id == user_id


# --- Deep Copy Isolation Tests ---

@pytest.mark.asyncio
async def test_returned_identity_is_deep_copy(in_memory_auth_identity_repo):
    """Modifying returned objects should not affect repository state."""
    created = await in_memory_auth_identity_repo.create_auth_identity(
        _create_auth_identity(provider_subject="copy_test")
    )

    fetched = await in_memory_auth_identity_repo.get_auth_identity(created.auth_identity_id)
    fetched.provider_subject = "hacked"
    fetched.password_hash = "hacked_hash"

    refetched = await in_memory_auth_identity_repo.get_auth_identity(created.auth_identity_id)
    assert refetched.provider_subject == "copy_test"
    assert refetched.password_hash != "hacked_hash"
