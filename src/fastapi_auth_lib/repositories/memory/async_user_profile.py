import uuid

from src.fastapi_auth_lib.core.constants import USER_ENTITY
from src.fastapi_auth_lib.core.exceptions import DuplicateEntityException
from src.fastapi_auth_lib.core.utils import _now
from src.fastapi_auth_lib.core.utils import normalize_email
from src.fastapi_auth_lib.models.base import UserStatus
from src.fastapi_auth_lib.models.user import UserProfile
from src.fastapi_auth_lib.repositories.async_user_profile import AsyncUserProfileRepository


class InMemoryAsyncUserProfileRepository(AsyncUserProfileRepository):
    """
    In-memory implementation of AsyncUserProfileRepository.

    Storage mirrors a SQL table with a UNIQUE index on email:
        _users:  user_id -> UserProfile
        _emails: normalized email -> user_id
    """

    def __init__(self) -> None:
        self._users: dict[uuid.UUID, UserProfile] = {}
        self._emails: dict[str, uuid.UUID] = {}

    async def create_user(self, user: UserProfile) -> UserProfile:
        email = normalize_email(user.email)

        if email in self._emails:
            raise DuplicateEntityException(
                entity_type=USER_ENTITY,
                description=f"A user with email '{email}' already exists",
            )

        user_id = user.user_id if user.user_id is not None else uuid.uuid4()
        if user_id in self._users:
            raise DuplicateEntityException(
                entity_type=USER_ENTITY,
                description=f"A user with email '{email}' already exists",
            )

        stored = user.model_copy(deep=True)
        stored.user_id = user_id
        stored.email = email
        stored.updated_at = None

        self._users[user_id] = stored
        self._emails[email] = user_id
        return stored.model_copy(deep=True)

    async def find_user_by_id(self, user_id: uuid.UUID) -> UserProfile | None:
        stored = self._users.get(user_id)
        return stored.model_copy(deep=True) if stored is not None else None

    async def find_user_by_email(self, email: str) -> UserProfile | None:
        user_id = self._emails.get(normalize_email(email))
        if user_id is None:
            return None
        stored = self._users.get(user_id)
        return stored.model_copy(deep=True) if stored is not None else None

    async def update_user(
        self,
        user_id: uuid.UUID,
        user: UserProfile,
    ) -> UserProfile | None:
        stored = self._users.get(user_id)
        if stored is None:
            return None

        new_email = normalize_email(user.email)
        owner = self._emails.get(new_email)
        if owner is not None and owner != user_id:
            raise DuplicateEntityException(
                entity_type=USER_ENTITY,
                description=f"Email '{new_email}' is already taken by another user",
            )

        old_email = stored.email

        updated = user.model_copy(deep=True)
        updated.user_id = user_id
        updated.email = new_email
        updated.created_at = stored.created_at
        updated.updated_at = _now()

        self._users[user_id] = updated
        if old_email != new_email:
            self._emails.pop(old_email, None)
            self._emails[new_email] = user_id

        return updated.model_copy(deep=True)

    async def delete_user(
        self,
        user_id: uuid.UUID,
        hard_delete: bool = False,
    ) -> None:
        stored = self._users.get(user_id)
        if stored is None:
            return

        if hard_delete:
            del self._users[user_id]
            self._emails.pop(stored.email, None)
        else:
            stored.status = UserStatus.DELETED
            stored.updated_at = _now()

    async def list_users(self) -> list[UserProfile]:
        return [user.model_copy(deep=True) for user in self._users.values()]
