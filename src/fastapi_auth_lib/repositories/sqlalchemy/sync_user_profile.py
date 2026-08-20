import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fastapi_auth_lib.core.exceptions import DuplicateEntityException
from fastapi_auth_lib.core.exceptions import EntityNotFoundException
from fastapi_auth_lib.core.utils import _now
from fastapi_auth_lib.models.base import USER_ENTITY
from fastapi_auth_lib.models.base import UserRole
from fastapi_auth_lib.models.base import UserStatus
from fastapi_auth_lib.models.user import UserProfile
from fastapi_auth_lib.repositories.db_models.db_user_profile import DBUserProfile
from fastapi_auth_lib.repositories.sync_user_profile_interface import IUserProfileRepository


class SQLAlchemyUserProfileRepository(IUserProfileRepository):
    """Synchronous SQLAlchemy implementation of IUserProfileRepository."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_user(self, user: UserProfile) -> UserProfile:
        self._assert_email_available(user.email)

        db_user = DBUserProfile(
            user_id=uuid.uuid4(),
            email=user.email,
            username=user.username,
            status=user.status,
            roles=[role.value for role in user.roles],
            created_at=_now(),
            updated_at=None,
        )

        self.session.add(db_user)

        try:
            self.session.flush()
        except IntegrityError as error:
            self.session.rollback()

            if self._email_exists(user.email):
                raise DuplicateEntityException(
                    field="email",
                    value=user.email,
                    entity_type=USER_ENTITY,
                ) from error

            raise error

        return self._to_dto(db_user)

    def get_user_by_id(self, user_id: uuid.UUID) -> UserProfile:
        db_user = self.session.get(DBUserProfile, user_id)

        if db_user is None:
            raise EntityNotFoundException(
                field="user_id",
                value=str(user_id),
                entity_type=USER_ENTITY,
            )

        return self._to_dto(db_user)

    def get_user_by_email(self, email: str) -> UserProfile:
        stmt = (
            select(DBUserProfile)
            .where(DBUserProfile.email == email)
            .limit(1)
        )

        result = self.session.execute(stmt)
        db_user = result.scalar_one_or_none()

        if db_user is None:
            raise EntityNotFoundException(
                field="email",
                value=email,
                entity_type=USER_ENTITY,
            )

        return self._to_dto(db_user)

    def update_user(self, user_id: uuid.UUID, user: UserProfile) -> UserProfile:
        db_user = self.session.get(DBUserProfile, user_id)

        if db_user is None or db_user.status == UserStatus.DELETED:
            raise EntityNotFoundException(
                field="user_id",
                value=str(user_id),
                entity_type=USER_ENTITY,
            )

        # Mutable fields
        db_user.username = user.username
        db_user.status = user.status
        db_user.roles = [role.value for role in user.roles]
        db_user.updated_at = _now()

        self.session.flush()

        return self._to_dto(db_user)

    def delete_user(self, user_id: uuid.UUID, hard_delete: bool = False) -> None:
        db_user = self.session.get(DBUserProfile, user_id)

        if db_user is None:
            raise EntityNotFoundException(
                field="user_id",
                value=str(user_id),
                entity_type=USER_ENTITY,
            )

        if hard_delete:
            self.session.delete(db_user)
        else:
            if db_user.status != UserStatus.DELETED:
                db_user.status = UserStatus.DELETED
                db_user.updated_at = _now()

        self.session.flush()

    def get_all_users(self) -> list[UserProfile]:
        stmt = select(DBUserProfile)

        result = self.session.execute(stmt)
        db_users = result.scalars().all()

        return [self._to_dto(db_user) for db_user in db_users]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _assert_email_available(self, email: str) -> None:
        if self._email_exists(email):
            raise DuplicateEntityException(
                field="email",
                value=email,
                entity_type=USER_ENTITY,
            )

    def _email_exists(self, email: str) -> bool:
        stmt = (
            select(DBUserProfile.user_id)
            .where(DBUserProfile.email == email)
            .limit(1)
        )

        result = self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @staticmethod
    def _to_dto(db_user: DBUserProfile) -> UserProfile:
        return UserProfile(
            user_id=db_user.user_id,
            email=db_user.email,
            username=db_user.username,
            status=db_user.status,
            roles=[UserRole(role) for role in db_user.roles],
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
        )
