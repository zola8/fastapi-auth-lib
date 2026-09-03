import asyncio

from src.fastapi_auth_lib.models.auth_identity import AuthIdentity
from src.fastapi_auth_lib.models.base import AuthProvider
from src.fastapi_auth_lib.models.user import UserProfile
from src.fastapi_auth_lib.repositories.memory.async_auth_identity import InMemoryAsyncAuthIdentityRepository
from src.fastapi_auth_lib.repositories.memory.async_user_profile import InMemoryAsyncUserProfileRepository

user_repo = InMemoryAsyncUserProfileRepository()
auth_repo = InMemoryAsyncAuthIdentityRepository()


async def main():
    user = UserProfile(username='test_user', email='email@email.com')
    user = await user_repo.create_user(user)

    auth_identity = AuthIdentity(
        user_id=user.user_id,
        provider=AuthProvider.PASSWORD,
        provider_subject='password',
        password_hash='hashed_password'
    )
    auth_identity = await auth_repo.create_auth_identity(auth_identity)

    print(user)
    print(auth_identity)


if __name__ == '__main__':
    asyncio.run(main())
