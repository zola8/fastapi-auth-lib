import asyncio

from src.fastapi_auth_lib.models.user import UserProfile
from src.fastapi_auth_lib.repositories.memory.async_user_profile import InMemoryAsyncUserProfileRepository

user_repo = InMemoryAsyncUserProfileRepository()


async def main():
    user = UserProfile(username='test_user', email='email@email.com')
    user = await user_repo.create_user(user)

    print(await user_repo.find_user_by_id(user.user_id))
    print(await user_repo.find_user_by_email(user.email))

    await user_repo.delete_user(user.user_id, hard_delete=True)

    print(await user_repo.list_users())


if __name__ == '__main__':
    asyncio.run(main())
