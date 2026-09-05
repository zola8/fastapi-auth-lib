import uuid

import pytest

from src.fastapi_auth_lib.core.constants import AUTH_IDENTITY_ENTITY
from src.fastapi_auth_lib.core.exceptions import DuplicateEntityException
from src.fastapi_auth_lib.models.auth_identity import AuthIdentity
from src.fastapi_auth_lib.models.base import AuthProvider
from src.fastapi_auth_lib.repositories.memory.async_auth_identity import InMemoryAsyncAuthIdentityRepository


@pytest.fixture
def auth_identity_repo():
    """Create a fresh in-memory auth identity repository."""
    return InMemoryAsyncAuthIdentityRepository()


def make_identity(
    user_id=None,
    provider=AuthProvider.PASSWORD,
    provider_subject="user@example.com",
    password_hash="hashed",
):
    """Helper to create an AuthIdentity with sensible defaults."""
    if user_id is None:
        user_id = uuid.uuid4()
    return AuthIdentity(
        user_id=user_id,
        provider=provider,
        provider_subject=provider_subject,
        password_hash=password_hash,
    )


class TestCreateAuthIdentity:
    """Tests for create_auth_identity."""

    @pytest.mark.asyncio
    async def test_create_success(self, auth_identity_repo):
        """Should store and return a copy with auth_identity_id set."""
        identity = make_identity()
        created = await auth_identity_repo.create_auth_identity(identity)

        assert created.auth_identity_id is not None
        assert created.user_id == identity.user_id
        assert created.provider == identity.provider
        assert created.provider_subject == identity.provider_subject
        assert created is not identity

        stored = await auth_identity_repo.find_auth_identity_by_id(created.auth_identity_id)
        assert stored is not None
        assert stored.auth_identity_id == created.auth_identity_id
        assert stored.user_id == created.user_id

    @pytest.mark.asyncio
    async def test_create_preserves_existing_id(self, auth_identity_repo):
        """Should respect a provided auth_identity_id."""
        identity = make_identity()
        identity.auth_identity_id = 42
        created = await auth_identity_repo.create_auth_identity(identity)

        assert created.auth_identity_id == 42
        stored = await auth_identity_repo.find_auth_identity_by_id(42)
        assert stored is not None

    @pytest.mark.asyncio
    async def test_duplicate_provider_subject_raises(self, auth_identity_repo):
        """(provider, provider_subject) uniqueness should be enforced."""
        identity1 = make_identity(provider_subject="dup@example.com")
        await auth_identity_repo.create_auth_identity(identity1)

        identity2 = make_identity(provider_subject="DUP@example.com")  # case-insensitive
        with pytest.raises(DuplicateEntityException) as exc_info:
            await auth_identity_repo.create_auth_identity(identity2)
        assert exc_info.value.entity_type == AUTH_IDENTITY_ENTITY

    @pytest.mark.asyncio
    async def test_duplicate_user_id_raises(self, auth_identity_repo):
        """One identity per user should be enforced."""
        uid = uuid.uuid4()
        identity1 = make_identity(user_id=uid, provider_subject="first@example.com")
        await auth_identity_repo.create_auth_identity(identity1)

        identity2 = make_identity(user_id=uid, provider_subject="second@example.com")
        with pytest.raises(DuplicateEntityException) as exc_info:
            await auth_identity_repo.create_auth_identity(identity2)
        assert exc_info.value.entity_type == AUTH_IDENTITY_ENTITY

    @pytest.mark.asyncio
    async def test_create_normalizes_provider_subject(self, auth_identity_repo):
        """provider_subject should be normalized (email lowercased/stripped)."""
        identity = make_identity(provider_subject="  User@Example.COM  ")
        created = await auth_identity_repo.create_auth_identity(identity)
        assert created.provider_subject == "user@example.com"

        stored = await auth_identity_repo.find_auth_identity_by_provider_subject(
            AuthProvider.PASSWORD, "USER@example.com"
        )
        assert stored is not None
        assert stored.provider_subject == "user@example.com"


class TestFindAuthIdentity:
    """Tests for find methods."""

    @pytest.mark.asyncio
    async def test_find_by_id_returns_none_if_missing(self, auth_identity_repo):
        """Should return None when no identity with that id exists."""
        result = await auth_identity_repo.find_auth_identity_by_id(999)
        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_user_id_returns_none_if_missing(self, auth_identity_repo):
        """Should return None when no identity for that user exists."""
        result = await auth_identity_repo.find_auth_identity_by_user_id(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_provider_subject_returns_none_if_missing(self, auth_identity_repo):
        """Should return None when no matching provider/subject exists."""
        result = await auth_identity_repo.find_auth_identity_by_provider_subject(
            AuthProvider.PASSWORD, "missing@example.com"
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_id_returns_deep_copy(self, auth_identity_repo):
        """Returned object should not be the internal reference."""
        identity = make_identity()
        created = await auth_identity_repo.create_auth_identity(identity)

        found = await auth_identity_repo.find_auth_identity_by_id(created.auth_identity_id)
        assert found is not created
        assert found == created

        found.provider_subject = "changed@example.com"
        again = await auth_identity_repo.find_auth_identity_by_id(created.auth_identity_id)
        assert again.provider_subject == created.provider_subject

    @pytest.mark.asyncio
    async def test_find_by_provider_subject_is_case_insensitive(self, auth_identity_repo):
        """Provider subject lookup should be case-insensitive."""
        await auth_identity_repo.create_auth_identity(make_identity())

        found = await auth_identity_repo.find_auth_identity_by_provider_subject(
            AuthProvider.PASSWORD, "USER@EXAMPLE.COM"
        )
        assert found is not None
        assert found.provider_subject == "user@example.com"


class TestUpdateAuthIdentity:
    """Tests for update_auth_identity."""

    @pytest.mark.asyncio
    async def test_update_existing_identity(self, auth_identity_repo):
        """Should update fields and return updated copy."""
        identity = make_identity()
        created = await auth_identity_repo.create_auth_identity(identity)

        update_data = make_identity(
            user_id=created.user_id,
            provider_subject="new@example.com",
            password_hash="new_hash",
        )
        updated = await auth_identity_repo.update_auth_identity(
            created.auth_identity_id, update_data
        )

        assert updated is not None
        assert updated.auth_identity_id == created.auth_identity_id
        assert updated.provider_subject == "new@example.com"
        assert updated.password_hash == "new_hash"
        assert updated.user_id == created.user_id

        stored = await auth_identity_repo.find_auth_identity_by_id(created.auth_identity_id)
        assert stored.provider_subject == "new@example.com"
        assert stored.password_hash == "new_hash"

    @pytest.mark.asyncio
    async def test_update_nonexistent_returns_none(self, auth_identity_repo):
        """Should return None if identity doesn't exist."""
        result = await auth_identity_repo.update_auth_identity(999, make_identity())
        assert result is None

    @pytest.mark.asyncio
    async def test_update_provider_subject_conflict_raises(self, auth_identity_repo):
        """Should raise DuplicateEntityException if new subject belongs to another identity."""
        id1 = make_identity(provider_subject="first@example.com")
        id2 = make_identity(provider_subject="second@example.com")
        created1 = await auth_identity_repo.create_auth_identity(id1)
        created2 = await auth_identity_repo.create_auth_identity(id2)

        update_data = make_identity(
            user_id=created2.user_id,
            provider_subject="first@example.com",
        )
        with pytest.raises(DuplicateEntityException) as exc_info:
            await auth_identity_repo.update_auth_identity(
                created2.auth_identity_id, update_data
            )
        assert exc_info.value.entity_type == AUTH_IDENTITY_ENTITY

    @pytest.mark.asyncio
    async def test_update_same_provider_subject_no_conflict(self, auth_identity_repo):
        """Updating with the same provider/subject should not raise."""
        identity = make_identity(provider_subject="same@example.com")
        created = await auth_identity_repo.create_auth_identity(identity)

        update_data = make_identity(
            user_id=created.user_id,
            provider_subject="same@example.com",
            password_hash="new_hash",
        )
        updated = await auth_identity_repo.update_auth_identity(
            created.auth_identity_id, update_data
        )
        assert updated is not None
        assert updated.provider_subject == "same@example.com"


class TestDeleteAuthIdentity:
    """Tests for delete_auth_identity."""

    @pytest.mark.asyncio
    async def test_delete_removes_identity(self, auth_identity_repo):
        """Should remove the identity."""
        identity = make_identity()
        created = await auth_identity_repo.create_auth_identity(identity)
        await auth_identity_repo.delete_auth_identity(created.auth_identity_id)

        assert await auth_identity_repo.find_auth_identity_by_id(created.auth_identity_id) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_is_noop(self, auth_identity_repo):
        """Deleting a missing identity should not raise."""
        await auth_identity_repo.delete_auth_identity(999)

    @pytest.mark.asyncio
    async def test_delete_then_recreate_allowed(self, auth_identity_repo):
        """After deletion, the same user/provider_subject can be created again."""
        identity = make_identity()
        created = await auth_identity_repo.create_auth_identity(identity)
        await auth_identity_repo.delete_auth_identity(created.auth_identity_id)

        # recreate with same user_id and provider_subject
        new_identity = make_identity(
            user_id=created.user_id,
            provider_subject=created.provider_subject,
        )
        recreated = await auth_identity_repo.create_auth_identity(new_identity)
        assert recreated.auth_identity_id is not None
