import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi_auth_lib.repositories.db_models import Base
from fastapi_auth_lib.repositories.memory.async_auth_identity import InMemoryAsyncAuthIdentityRepository
from fastapi_auth_lib.repositories.memory.async_user_profile import InMemoryAsyncUserProfileRepository
from fastapi_auth_lib.repositories.sqlalchemy.sync_auth_identity import SQLAlchemyIdentityRepository
from fastapi_auth_lib.repositories.sqlalchemy.sync_user_profile import SQLAlchemyUserProfileRepository

VALID_EMAIL = "user@example.com"
USER_ID = "00000000-0000-4000-8000-000000000001"


@pytest_asyncio.fixture
async def in_memory_async_user_repo():
    """Provides a fresh InMemoryUserRepository instance for each test."""
    return InMemoryAsyncUserProfileRepository()


@pytest_asyncio.fixture
async def in_memory_async_auth_identity_repo():
    """Provides a fresh InMemoryAuthIdentityRepository instance for each test."""
    return InMemoryAsyncAuthIdentityRepository()


@pytest.fixture
def sql_sync_user_repo():
    """Provides a fresh SQLAlchemyUserProfileRepository by in-memory SQLite."""
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Create all tables (user_profile + auth_identity share the same Base)
    Base.metadata.create_all(engine)

    SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionFactory()

    repo = SQLAlchemyUserProfileRepository(session)

    yield repo

    # Teardown
    session.close()
    engine.dispose()


@pytest.fixture
def sql_sync_identity_repo():
    """Provides a fresh SQLAlchemyIdentityRepository backed by in-memory SQLite."""
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Create all tables (auth_identity + user_profile share the same Base)
    Base.metadata.create_all(engine)

    SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionFactory()

    repo = SQLAlchemyIdentityRepository(session)

    yield repo

    # Teardown
    session.close()
    engine.dispose()
