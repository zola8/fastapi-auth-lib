import asyncio

from fastapi_auth_lib.core.exceptions import EntityNotFoundException
from fastapi_auth_lib.models.user import UserProfile
from fastapi_auth_lib.repositories.memory.user_profile import InMemoryUserProfileRepository

user_repo = InMemoryUserProfileRepository()


async def main():
    user = UserProfile(username='test_user', email='email@email.com')
    user = await user_repo.create_user(user)

    print(await user_repo.get_user_by_id(user.user_id))
    await user_repo.delete_user(user.user_id, hard_delete=True)

    try:
        await user_repo.get_user_by_id(user.user_id)
    except EntityNotFoundException:
        print('user not found')


if __name__ == '__main__':
    asyncio.run(main())
