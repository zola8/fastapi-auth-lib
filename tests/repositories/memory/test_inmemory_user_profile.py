import uuid

import pytest

from src.fastapi_auth_lib.core.constants import USER_ENTITY
from src.fastapi_auth_lib.core.exceptions import DuplicateEntityException
from src.fastapi_auth_lib.models.base import UserRole
from src.fastapi_auth_lib.models.base import UserStatus
from src.fastapi_auth_lib.models.user import UserProfile
from src.fastapi_auth_lib.repositories.memory.async_user_profile import InMemoryAsyncUserProfileRepository


@pytest.fixture
def user_repo():
    """Create a fresh in-memory repository."""
    return InMemoryAsyncUserProfileRepository()


def make_user(email="user@example.com", username="user", roles=None, status=UserStatus.ACTIVE):
    """Helper to create a UserProfile with defaults."""

    return UserProfile(
        email=email,
        username=username,
        roles=roles if roles is not None else [UserRole.USER],
        status=status,
    )


class TestCreateUser:
    """Tests for create_user."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_repo):
        """Should store the user and return a copy with user_id set."""
        user = make_user()
        created = await user_repo.create_user(user)

        assert created.user_id is not None
        assert created.email == user.email
        assert created.username == user.username
        assert created is not user

        stored = await user_repo.find_user_by_id(created.user_id)
        assert stored is not None
        assert stored.user_id == created.user_id
        assert stored.email == created.email

    @pytest.mark.asyncio
    async def test_create_user_preserves_existing_id(self, user_repo):
        """Should respect a provided user_id."""
        uid = uuid.uuid4()
        user = make_user()
        user.user_id = uid
        created = await user_repo.create_user(user)

        assert created.user_id == uid
        stored = await user_repo.find_user_by_id(uid)
        assert stored is not None
        assert stored.user_id == uid

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_raises(self, user_repo):
        """Should raise DuplicateEntityException if email already exists."""
        user1 = make_user(email="dup@example.com")
        await user_repo.create_user(user1)

        user2 = make_user(email="DUP@example.com")  # case-insensitive
        with pytest.raises(DuplicateEntityException) as exc_info:
            await user_repo.create_user(user2)
        assert "dup@example.com" in str(exc_info.value)
        assert exc_info.value.entity_type == USER_ENTITY

    @pytest.mark.asyncio
    async def test_create_user_duplicate_id_raises(self, user_repo):
        """Should raise if the provided user_id already exists."""
        uid = uuid.uuid4()
        user1 = make_user(email="first@example.com")
        user1.user_id = uid
        await user_repo.create_user(user1)

        user2 = make_user(email="second@example.com")
        user2.user_id = uid
        with pytest.raises(DuplicateEntityException) as exc_info:
            await user_repo.create_user(user2)
        assert exc_info.value.entity_type == USER_ENTITY

    @pytest.mark.asyncio
    async def test_create_user_normalizes_email(self, user_repo):
        """Email should be normalized (lowercase, stripped) before storing."""
        user = make_user(email="  User@Example.COM  ")
        created = await user_repo.create_user(user)

        assert created.email == "user@example.com"
        stored = await user_repo.find_user_by_email("USER@example.com")
        assert stored is not None

    @pytest.mark.asyncio
    async def test_create_user_sets_updated_at_none(self, user_repo):
        """updated_at should be None on creation."""
        user = make_user()
        user.updated_at = "2026-01-01T00:00:00Z"  # force non-None
        created = await user_repo.create_user(user)
        assert created.updated_at is None


class TestFindUser:
    """Tests for find_user_by_id and find_user_by_email."""

    @pytest.mark.asyncio
    async def test_find_by_id_returns_none_if_missing(self, user_repo):
        """Should return None when no user with that id exists."""
        result = await user_repo.find_user_by_id(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_email_returns_none_if_missing(self, user_repo):
        """Should return None when no user with that email exists."""
        result = await user_repo.find_user_by_email("nonexistent@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_id_returns_deep_copy(self, user_repo):
        """Returned object should not be the internal reference."""
        user = make_user()
        created = await user_repo.create_user(user)

        found = await user_repo.find_user_by_id(created.user_id)
        assert found is not created
        assert found == created

        # Modifying returned object should not affect storage
        found.username = "changed"
        again = await user_repo.find_user_by_id(created.user_id)
        assert again.username == created.username

    @pytest.mark.asyncio
    async def test_find_by_email_returns_deep_copy(self, user_repo):
        """Same as above but by email."""
        user = make_user()
        await user_repo.create_user(user)

        found = await user_repo.find_user_by_email(user.email)
        found.username = "changed"
        again = await user_repo.find_user_by_email(user.email)
        assert again.username == user.username

    @pytest.mark.asyncio
    async def test_find_by_email_is_case_insensitive(self, user_repo):
        """Should find user regardless of email case."""
        await user_repo.create_user(make_user(email="user@example.com"))

        found = await user_repo.find_user_by_email("USER@EXAMPLE.COM")
        assert found is not None
        assert found.email == "user@example.com"


class TestUpdateUser:
    """Tests for update_user."""

    @pytest.mark.asyncio
    async def test_update_existing_user(self, user_repo):
        """Should update fields and return updated copy."""
        user = make_user(username="old_username")
        created = await user_repo.create_user(user)

        update_data = make_user(username="new_username", email="new@example.com")
        updated = await user_repo.update_user(created.user_id, update_data)

        assert updated is not None
        assert updated.user_id == created.user_id
        assert updated.username == "new_username"
        assert updated.email == "new@example.com"
        assert updated.created_at == created.created_at
        assert updated.updated_at is not None

        stored = await user_repo.find_user_by_id(created.user_id)
        assert stored.username == "new_username"
        assert stored.email == "new@example.com"

    @pytest.mark.asyncio
    async def test_update_nonexistent_user_returns_none(self, user_repo):
        """Should return None if user doesn't exist."""
        uid = uuid.uuid4()
        result = await user_repo.update_user(uid, make_user())
        assert result is None

    @pytest.mark.asyncio
    async def test_update_email_conflict_raises(self, user_repo):
        """Should raise DuplicateEntityException if new email belongs to another user."""
        user1 = await user_repo.create_user(make_user(email="first@example.com"))
        user2 = await user_repo.create_user(make_user(email="second@example.com"))

        update_data = make_user(email="first@example.com")
        with pytest.raises(DuplicateEntityException) as exc_info:
            await user_repo.update_user(user2.user_id, update_data)
        assert exc_info.value.entity_type == USER_ENTITY

    @pytest.mark.asyncio
    async def test_update_same_email_no_conflict(self, user_repo):
        """Updating with same email should not raise."""
        user = await user_repo.create_user(make_user(email="same@example.com"))
        update_data = make_user(email="same@example.com", username="new_name")
        updated = await user_repo.update_user(user.user_id, update_data)
        assert updated is not None

    @pytest.mark.asyncio
    async def test_update_preserves_created_at(self, user_repo):
        """created_at should remain unchanged."""
        user = await user_repo.create_user(make_user())
        update_data = make_user(username="different")
        updated = await user_repo.update_user(user.user_id, update_data)
        assert updated.created_at == user.created_at

    @pytest.mark.asyncio
    async def test_update_sets_updated_at(self, user_repo):
        """updated_at should be set to a new timestamp."""
        user = await user_repo.create_user(make_user())
        update_data = make_user()
        updated = await user_repo.update_user(user.user_id, update_data)
        assert updated.updated_at is not None
        assert updated.updated_at != user.updated_at


class TestDeleteUser:
    """Tests for delete_user."""

    @pytest.mark.asyncio
    async def test_soft_delete_sets_status_deleted(self, user_repo):
        """Soft delete should set status to DELETED and keep user."""
        user = await user_repo.create_user(make_user())
        await user_repo.delete_user(user.user_id)

        stored = await user_repo.find_user_by_id(user.user_id)
        assert stored is not None
        assert stored.status == UserStatus.DELETED
        assert stored.updated_at is not None

    @pytest.mark.asyncio
    async def test_hard_delete_removes_user(self, user_repo):
        """Hard delete should remove user from storage."""
        user = await user_repo.create_user(make_user())
        await user_repo.delete_user(user.user_id, hard_delete=True)

        assert await user_repo.find_user_by_id(user.user_id) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_user_is_noop(self, user_repo):
        """Deleting a missing user should not raise."""
        await user_repo.delete_user(uuid.uuid4())
        await user_repo.delete_user(uuid.uuid4(), hard_delete=True)

    @pytest.mark.asyncio
    async def test_soft_delete_then_find_by_email(self, user_repo):
        """Soft-deleted user should still be findable by email."""
        user = await user_repo.create_user(make_user(email="soft@example.com"))
        await user_repo.delete_user(user.user_id)
        found = await user_repo.find_user_by_email("soft@example.com")
        assert found is not None
        assert found.status == UserStatus.DELETED

    @pytest.mark.asyncio
    async def test_hard_delete_removes_email_mapping(self, user_repo):
        """After hard delete, email should not resolve."""
        user = await user_repo.create_user(make_user(email="hard@example.com"))
        await user_repo.delete_user(user.user_id, hard_delete=True)
        assert await user_repo.find_user_by_email("hard@example.com") is None


class TestListUsers:
    """Tests for list_users."""

    @pytest.mark.asyncio
    async def test_list_empty(self, user_repo):
        """Should return empty list when no users exist."""
        assert await user_repo.list_users() == []

    @pytest.mark.asyncio
    async def test_list_returns_all_users(self, user_repo):
        """Should return all created users."""
        u1 = await user_repo.create_user(make_user(email="one@example.com"))
        u2 = await user_repo.create_user(make_user(email="two@example.com"))
        users = await user_repo.list_users()
        assert len(users) == 2
        assert {u.user_id for u in users} == {u1.user_id, u2.user_id}

    @pytest.mark.asyncio
    async def test_list_returns_deep_copies(self, user_repo):
        """Modifying returned list should not affect storage."""
        await user_repo.create_user(make_user())
        users = await user_repo.list_users()
        users[0].username = "changed"
        again = await user_repo.list_users()
        assert again[0].username != "changed"
