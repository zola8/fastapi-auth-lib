from uuid import UUID

from src.fastapi_auth_lib.core.constants import USER_ENTITY
from src.fastapi_auth_lib.core.exceptions import EntityNotFoundException
from src.fastapi_auth_lib.models.user import UserProfile


class AsyncUserService:

    def __init__(self, user_repo) -> None:
        self._user_repo = user_repo

    async def create_user(self, user: UserProfile) -> UserProfile:
        return await self._user_repo.create_user(user)

    async def get_user(self, user_id: UUID) -> UserProfile:
        user = await self._user_repo.find_user_by_id(user_id)
        if user is None:
            raise EntityNotFoundException(
                entity_type=USER_ENTITY,
                description=f"No user found with id '{user_id}'",
            )
        return user

    async def list_users(self) -> list[UserProfile]:
        return await self._user_repo.list_users()

    async def delete_user(self, user_id: UUID) -> None:
        await self.get_user(user_id)  # throw error if not found
        await self._user_repo.delete_user(user_id, hard_delete=False)

    async def update_user(self, user_id: UUID, user: UserProfile) -> UserProfile:
        await self.get_user(user_id)
        updated = await self._user_repo.update_user(user_id, user)
        if updated is None:  # deleted between the check and the update
            raise EntityNotFoundException(
                entity_type=USER_ENTITY,
                description=f"No user found with id '{user_id}'",
            )
        return updated
