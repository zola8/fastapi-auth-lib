import pytest_asyncio

from fastapi_auth_lib.repositories.memory.auth_identity import InMemoryAuthIdentityRepository
from fastapi_auth_lib.repositories.memory.user_profile import InMemoryUserProfileRepository

VALID_EMAIL = "user@example.com"
USER_ID = "00000000-0000-4000-8000-000000000001"


@pytest_asyncio.fixture
async def in_memory_user_repo():
    """Provides a fresh InMemoryUserRepository instance for each test."""
    return InMemoryUserProfileRepository()


@pytest_asyncio.fixture
async def in_memory_auth_identity_repo():
    """Provides a fresh InMemoryAuthIdentityRepository instance for each test."""
    return InMemoryAuthIdentityRepository()
