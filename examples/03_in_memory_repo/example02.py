import asyncio

from fastapi_auth_lib.models.auth_identity import AuthIdentity
from fastapi_auth_lib.models.base import AuthProvider
from fastapi_auth_lib.models.user import UserProfile
from fastapi_auth_lib.repositories.memory.auth_identity import InMemoryAuthIdentityRepository
from fastapi_auth_lib.repositories.memory.user_profile import InMemoryUserProfileRepository

user_repo = InMemoryUserProfileRepository()
auth_repo = InMemoryAuthIdentityRepository()


async def main():
    user = UserProfile(username='test_user', email='email@email.com')
    user = await user_repo.create_user(user)

    auth_identity = AuthIdentity(user_id=user.user_id, provider=AuthProvider.PASSWORD, provider_subject='password',
                                 password_hash='hashed_password')
    auth_identity = await auth_repo.create_auth_identity(auth_identity)

    print(user)
    print(auth_identity)


if __name__ == '__main__':
    asyncio.run(main())
