import uuid

import pytest

from src.fastapi_auth_lib.core.constants import USER_ENTITY
from src.fastapi_auth_lib.core.exceptions import EntityNotFoundException
from src.fastapi_auth_lib.models.base import UserRole
from src.fastapi_auth_lib.models.base import UserStatus
from src.fastapi_auth_lib.models.user import UserProfile


def make_user(
    email="user@example.com",
    username="user",
    roles=None,
    status=UserStatus.ACTIVE,
):
    """Create a UserProfile with sensible defaults."""
    return UserProfile(
        email=email,
        username=username,
        roles=roles if roles is not None else [UserRole.USER],
        status=status,
    )


class TestAsyncUserService:
    """Tests for AsyncUserService."""

    @pytest.mark.asyncio
    async def test_create_user_returns_created(self, user_service):
        user = make_user()
        created = await user_service.create_user(user)
        assert created.user_id is not None
        assert created.email == user.email

        fetched = await user_service.get_user(created.user_id)
        assert fetched.user_id == created.user_id
        assert fetched.email == created.email
        assert fetched.username == created.username
        assert fetched.status == created.status
        assert fetched.roles == created.roles

    @pytest.mark.asyncio
    async def test_get_user_existing(self, user_service):
        user = make_user()
        created = await user_service.create_user(user)
        fetched = await user_service.get_user(created.user_id)
        assert fetched.user_id == created.user_id
        assert fetched.email == created.email
        assert fetched.username == created.username

    @pytest.mark.asyncio
    async def test_get_user_not_found_raises(self, user_service):
        uid = uuid.uuid4()
        with pytest.raises(EntityNotFoundException) as exc_info:
            await user_service.get_user(uid)
        assert exc_info.value.entity_type == USER_ENTITY
        assert str(uid) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_users_empty(self, user_service):
        users = await user_service.list_users()
        assert users == []

    @pytest.mark.asyncio
    async def test_list_users_returns_all(self, user_service):
        u1 = await user_service.create_user(make_user(email="one@example.com"))
        u2 = await user_service.create_user(make_user(email="two@example.com"))
        users = await user_service.list_users()
        assert len(users) == 2
        assert {u.user_id for u in users} == {u1.user_id, u2.user_id}

    @pytest.mark.asyncio
    async def test_delete_user_existing(self, user_service):
        user = await user_service.create_user(make_user())
        await user_service.delete_user(user.user_id)

        stored = await user_service.get_user(user.user_id)
        assert stored.status == UserStatus.DELETED

    @pytest.mark.asyncio
    async def test_delete_user_not_found_raises(self, user_service):
        uid = uuid.uuid4()
        with pytest.raises(EntityNotFoundException):
            await user_service.delete_user(uid)

    @pytest.mark.asyncio
    async def test_update_user_existing(self, user_service):
        created = await user_service.create_user(make_user(username="old"))
        update_data = make_user(username="new", email="new@example.com")
        updated = await user_service.update_user(created.user_id, update_data)
        assert updated.user_id == created.user_id
        assert updated.username == "new"
        assert updated.email == "new@example.com"

        fetched = await user_service.get_user(created.user_id)
        assert fetched.username == "new"

    @pytest.mark.asyncio
    async def test_update_user_not_found_raises(self, user_service):
        uid = uuid.uuid4()
        with pytest.raises(EntityNotFoundException):
            await user_service.update_user(uid, make_user())

    @pytest.mark.asyncio
    async def test_update_user_repo_returns_none_after_check(self, user_service, user_repo, monkeypatch):
        """
        Simulate a race condition: service's get_user succeeds, but the repo's update_user
        returns None because the user was deleted in between.
        """
        created = await user_service.create_user(make_user())

        # Monkeypatch repo.update_user to return None for this user
        original_update = user_repo.update_user

        async def fake_update(user_id, user):
            if user_id == created.user_id:
                return None
            return await original_update(user_id, user)

        monkeypatch.setattr(user_repo, "update_user", fake_update)

        with pytest.raises(EntityNotFoundException) as exc_info:
            await user_service.update_user(created.user_id, make_user())
        assert str(created.user_id) in str(exc_info.value)
