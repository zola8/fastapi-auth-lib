import uuid

from fastapi_auth_lib.models.user import UserProfile
from fastapi_auth_lib.repositories.user_repo_interface import UserRepository


class SQLAlchemyUserRepository(UserRepository):
    async def create_user(self, user: UserProfile) -> UserProfile:
        pass

    async def get_user_by_id(self, user_id: uuid.UUID) -> UserProfile:
        pass

    async def get_user_by_email(self, email: str) -> UserProfile:
        pass

    async def update_user(self, user_id: uuid.UUID, user: UserProfile) -> UserProfile:
        pass

    async def delete_user(self, user_id: uuid.UUID, hard_delete: bool = False) -> None:
        pass

    async def get_all_users(self) -> list[UserProfile]:
        pass
