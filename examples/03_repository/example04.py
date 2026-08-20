from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi_auth_lib.models.auth_identity import AuthIdentity
from fastapi_auth_lib.models.base import AuthProvider
from fastapi_auth_lib.models.base import UserRole
from fastapi_auth_lib.models.base import UserStatus
from fastapi_auth_lib.models.user import UserProfile
from fastapi_auth_lib.repositories.db_models.db_base import Base
from fastapi_auth_lib.repositories.sqlalchemy.sync_auth_identity import SQLAlchemyIdentityRepository
from fastapi_auth_lib.repositories.sqlalchemy.sync_user_profile import SQLAlchemyUserProfileRepository


def main() -> None:
    # 1. Set up sync engine + session factory
    engine = create_engine("sqlite:///auth_demo.db", echo=False)
    SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)

    # 2. Create tables
    Base.metadata.create_all(engine)

    # 3. Single transaction for both operations
    with SessionFactory() as session:
        user_repo = SQLAlchemyUserProfileRepository(session)
        identity_repo = SQLAlchemyIdentityRepository(session)

        try:
            # --- CREATE USER ---
            new_user = UserProfile(
                email="alice@example.com",
                username="alice",
                roles=[UserRole.USER],
                status=UserStatus.ACTIVE,
            )
            created_user = user_repo.create_user(new_user)
            print(f"User created: {created_user.user_id} | {created_user.email}")

            # --- CREATE AUTH IDENTITY ---
            new_identity = AuthIdentity(
                user_id=created_user.user_id,
                provider=AuthProvider.PASSWORD,
                provider_subject="alice@example.com",
                password_hash="hashed_password",
            )
            created_identity = identity_repo.create_auth_identity(new_identity)
            print(
                f"Auth identity created: id={created_identity.auth_identity_id} | provider={created_identity.provider}")

            # --- COMMIT BOTH IN ONE TRANSACTION ---
            session.commit()
            print("Transaction committed successfully")

        except Exception as e:
            session.rollback()
            print(f"Transaction rolled back: {e}")
            raise

    # 4. Verify in a separate session
    with SessionFactory() as session:
        user_repo = SQLAlchemyUserProfileRepository(session)
        identity_repo = SQLAlchemyIdentityRepository(session)

        fetched_user = user_repo.get_user_by_email("alice@example.com")
        fetched_identity = identity_repo.get_auth_identity_by_user_id(fetched_user.user_id)

        print(f"\nVerification:")
        print(f"  User: {fetched_user.username} ({fetched_user.status})")
        print(f"  Identity: provider={fetched_identity.provider}, subject={fetched_identity.provider_subject}")
        print(f"  Created at: {fetched_identity.created_at}")

    engine.dispose()


if __name__ == "__main__":
    main()
