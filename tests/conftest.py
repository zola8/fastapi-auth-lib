import pytest_asyncio

from fastapi_auth_lib.repositories.memory.async_auth_identity import InMemoryAsyncAuthIdentityRepository
from fastapi_auth_lib.repositories.memory.async_user_profile import InMemoryAsyncUserProfileRepository

VALID_EMAIL = "user@example.com"
USER_ID = "00000000-0000-4000-8000-000000000001"


@pytest_asyncio.fixture
async def in_memory_user_repo():
    """Provides a fresh InMemoryUserRepository instance for each test."""
    return InMemoryAsyncUserProfileRepository()


@pytest_asyncio.fixture
async def in_memory_auth_identity_repo():
    """Provides a fresh InMemoryAuthIdentityRepository instance for each test."""
    return InMemoryAsyncAuthIdentityRepository()
