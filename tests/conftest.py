import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

# Import models so they register with Base.metadata before create_all
from src.fastapi_auth_lib.repositories.db_models import db_auth_identity  # noqa: F401
from src.fastapi_auth_lib.repositories.db_models import db_user_profile  # noqa: F401
from src.fastapi_auth_lib.repositories.db_models.db_base import Base
from src.fastapi_auth_lib.repositories.sql.async_auth_identity import SqlAsyncAuthIdentityRepository
from src.fastapi_auth_lib.repositories.sql.async_user_profile import SqlAsyncUserProfileRepository
from src.fastapi_auth_lib.services.async_auth_service import AsyncAuthService
from src.fastapi_auth_lib.services.async_user_service import AsyncUserService
from src.fastapi_auth_lib.services.password_hasher.plain_text_hasher import PlaintextHasher
from src.fastapi_auth_lib.services.token.jwt_token_service import JwtTokenService


@pytest_asyncio.fixture(scope="function")
async def engine():
    """In-memory SQLite shared across connections via StaticPool."""
    eng = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    @event.listens_for(eng.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield eng

    await eng.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(engine) -> AsyncSession:
    """A session bound to the in-memory engine. Rolls back after each test."""
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as sess:
        yield sess
        await sess.rollback()


@pytest_asyncio.fixture(scope="function")
async def user_repo(session) -> SqlAsyncUserProfileRepository:
    return SqlAsyncUserProfileRepository(session)


@pytest_asyncio.fixture(scope="function")
async def auth_identity_repo(session) -> SqlAsyncAuthIdentityRepository:
    return SqlAsyncAuthIdentityRepository(session)


@pytest_asyncio.fixture(scope="function")
async def both_repos(session):
    """Provides both repos sharing the same session for integration tests."""
    return (
        SqlAsyncUserProfileRepository(session),
        SqlAsyncAuthIdentityRepository(session),
    )


@pytest_asyncio.fixture
def user_service(user_repo):
    """Provide an AsyncUserService instance using the SqlAsyncUserProfileRepository in-memory repo."""
    return AsyncUserService(user_repo)


@pytest_asyncio.fixture
def password_hasher():
    return PlaintextHasher()


TEST_SECRET = "test-secret-which-is-long-enough"
TEST_ISSUER = "test-issuer"


@pytest_asyncio.fixture
def token_service():
    return JwtTokenService(secret=TEST_SECRET, issuer=TEST_ISSUER)


@pytest_asyncio.fixture
def auth_service(user_service, auth_identity_repo, password_hasher, token_service):
    return AsyncAuthService(
        user_service=user_service,
        identity_repo=auth_identity_repo,
        password_hasher=password_hasher,
        token_service=token_service,
    )
