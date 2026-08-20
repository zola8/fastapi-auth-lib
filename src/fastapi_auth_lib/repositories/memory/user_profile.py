import asyncio
import uuid
from typing import Dict

from fastapi_auth_lib.core.exceptions import DuplicateEntityException
from fastapi_auth_lib.core.exceptions import EntityNotFoundException
from fastapi_auth_lib.core.utils import _now
from fastapi_auth_lib.models.base import USER_ENTITY
from fastapi_auth_lib.models.base import UserStatus
from fastapi_auth_lib.models.user import UserProfile
from fastapi_auth_lib.repositories.user_profile_interface import IUserProfileRepository


class InMemoryUserProfileRepository(IUserProfileRepository):
    """Own in-memory implementation of UserProfileRepository."""

    def __init__(self) -> None:
        self._users: Dict[uuid.UUID, UserProfile] = {}
        self._user_ids_by_email: Dict[str, uuid.UUID] = {}
        self._lock = asyncio.Lock()

    async def create_user(self, user: UserProfile) -> UserProfile:
        async with self._lock:
            self._assert_email_available(user.email)

            user_id = uuid.uuid4()
            new_user = user.model_copy(deep=True)
            new_user.user_id = user_id
            new_user.email = user.email
            new_user.created_at = _now()
            new_user.updated_at = None

            self._users[user_id] = new_user
            self._index_user(new_user)

            return new_user.model_copy(deep=True)

    async def get_user_by_id(self, user_id: uuid.UUID) -> UserProfile:
        async with self._lock:
            user = self._get_user_or_raise(user_id)
            return user.model_copy(deep=True)

    async def get_user_by_email(self, email: str) -> UserProfile:
        async with self._lock:
            user_id = self._user_ids_by_email.get(email)
            user = self._users.get(user_id) if user_id else None

            if user is None:
                raise EntityNotFoundException(
                    field="email",
                    value=email,
                    entity_type=USER_ENTITY,
                )

            return user.model_copy(deep=True)

    async def update_user(self, user_id: uuid.UUID, new_user_profile: UserProfile) -> UserProfile:
        async with self._lock:
            existing_user = self._users.get(user_id)

            if existing_user is None or existing_user.status == UserStatus.DELETED:
                raise EntityNotFoundException(
                    field="user_id",
                    value=str(user_id),
                    entity_type=USER_ENTITY,
                )

            updated_user = new_user_profile.model_copy(deep=True)
            # mutable fields - username, status, roles
            updated_user.roles = list(new_user_profile.roles)

            # immutable fields
            updated_user.user_id = user_id
            updated_user.email = existing_user.email
            updated_user.created_at = existing_user.created_at

            updated_user.updated_at = _now()
            self._users[user_id] = updated_user
            return updated_user.model_copy(deep=True)

    async def delete_user(self, user_id: uuid.UUID, hard_delete: bool = False) -> None:
        async with self._lock:
            existing_user = self._users.get(user_id)

            if existing_user is None:
                raise EntityNotFoundException(
                    field="user_id",
                    value=str(user_id),
                    entity_type=USER_ENTITY,
                )

            if hard_delete:
                self._deindex_user(existing_user)
                del self._users[user_id]
                return

            if existing_user.status == UserStatus.DELETED:
                return

            deleted_user = existing_user.model_copy(deep=True)
            deleted_user.status = UserStatus.DELETED
            deleted_user.updated_at = _now()

            self._users[user_id] = deleted_user

    async def get_all_users(self) -> list[UserProfile]:
        async with self._lock:
            return [
                user.model_copy(deep=True)
                for user in self._users.values()
            ]

    def _get_user_or_raise(self, user_id: uuid.UUID) -> UserProfile:
        user = self._users.get(user_id)

        if user is None:
            raise EntityNotFoundException(
                field="user_id",
                value=str(user_id),
                entity_type=USER_ENTITY,
            )

        return user

    def _assert_email_available(self, email: str) -> None:
        if email in self._user_ids_by_email:
            raise DuplicateEntityException(
                field="email",
                value=email,
                entity_type=USER_ENTITY,
            )

    def _index_user(self, user: UserProfile) -> None:
        if user.user_id is None:
            return
        self._user_ids_by_email[user.email] = user.user_id

    def _deindex_user(self, user: UserProfile) -> None:
        if self._user_ids_by_email.get(user.email) == user.user_id:
            del self._user_ids_by_email[user.email]
