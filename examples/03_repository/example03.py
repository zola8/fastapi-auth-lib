import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from fastapi_auth_lib.models.base import UserRole
from fastapi_auth_lib.models.base import UserStatus
from fastapi_auth_lib.models.user import UserProfile
from fastapi_auth_lib.repositories.db_models.db_base import Base
from fastapi_auth_lib.repositories.sqlalchemy.async_user_profile import SQLAlchemyAsyncUserProfileRepository


async def main() -> None:
    # 1. Set up async engine + session factory
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # 2. Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 3. Use the repository inside a session scope
    async with async_session_factory() as session:
        repo = SQLAlchemyAsyncUserProfileRepository(session)

        # --- CREATE ---
        new_user = UserProfile(
            email="alice@example.com",
            username="alice",
            roles=[UserRole.USER],
            status=UserStatus.ACTIVE,
        )
        created = await repo.create_user(new_user)
        print(f"Created: {created.user_id} | {created.email}")

        # --- GET BY ID ---
        fetched = await repo.get_user_by_id(created.user_id)
        print(f"Fetched by ID: {fetched.username}")

        # --- UPDATE ---
        updated_profile = UserProfile(
            email="alice@example.com",  # immutable, ignored
            username="alice_updated",
            roles=[UserRole.USER, UserRole.ADMIN],
            status=UserStatus.ACTIVE,
        )
        updated = await repo.update_user(created.user_id, updated_profile)
        print(f"Updated: {updated.username} | roles={updated.roles}")

        # --- GET ALL ---
        all_users = await repo.get_all_users()
        print(f"Total users: {len(all_users)}")

        # --- SOFT DELETE ---
        await repo.delete_user(created.user_id, hard_delete=False)
        print("Soft deleted successfully")

        # Commit the transaction
        await session.commit()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
