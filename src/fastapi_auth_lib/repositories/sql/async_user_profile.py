import uuid

from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.fastapi_auth_lib.core.constants import USER_ENTITY
from src.fastapi_auth_lib.core.exceptions import DuplicateEntityException
from src.fastapi_auth_lib.core.utils import _now
from src.fastapi_auth_lib.models.base import UserRole
from src.fastapi_auth_lib.models.base import UserStatus
from src.fastapi_auth_lib.models.user import UserProfile
from src.fastapi_auth_lib.repositories.async_user_profile import AsyncUserProfileRepository
from src.fastapi_auth_lib.repositories.db_models.db_user_profile import DBUserProfile


def _to_domain(row: DBUserProfile) -> UserProfile:
    """Map a DB row to the domain model."""
    return UserProfile(
        user_id=row.user_id,
        username=row.username,
        email=row.email,
        status=UserStatus(row.status),
        roles=[UserRole(r) for r in (row.roles or [])],
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAsyncUserProfileRepository(AsyncUserProfileRepository):
    """
    SQLAlchemy async implementation of AsyncUserProfileRepository.

    Contract:
    - The session is injected and owned by the caller.
    - This repository flushes but NEVER commits; the service owns the transaction boundary.
    - Input is trusted: email and other values must already be normalized
      by the API or service layer.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_user(self, user: UserProfile) -> UserProfile:
        db_user = DBUserProfile(
            user_id=user.user_id or uuid.uuid4(),
            email=user.email,
            username=user.username,
            status=user.status,
            roles=[r.value for r in user.roles],
            created_at=user.created_at,
            updated_at=None,
        )

        try:
            async with self._session.begin_nested():
                self._session.add(db_user)
                await self._session.flush()
        except IntegrityError as exc:
            raise DuplicateEntityException(
                entity_type=USER_ENTITY,
                description=f"A user with email '{user.email}' already exists",
            ) from exc

        return _to_domain(db_user)

    async def find_user_by_id(self, user_id: uuid.UUID) -> UserProfile | None:
        row = await self._session.get(DBUserProfile, user_id)
        return _to_domain(row) if row is not None else None

    async def find_user_by_email(self, email: str) -> UserProfile | None:
        stmt = select(DBUserProfile).where(DBUserProfile.email == email)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _to_domain(row) if row is not None else None

    async def update_user(
        self,
        user_id: uuid.UUID,
        user: UserProfile,
    ) -> UserProfile | None:
        existing = await self._session.get(DBUserProfile, user_id)
        if existing is None:
            return None

        if user.email != existing.email:
            stmt = select(DBUserProfile.user_id).where(
                DBUserProfile.email == user.email,
                DBUserProfile.user_id != user_id,
            )
            conflict = (await self._session.execute(stmt)).scalar_one_or_none()
            if conflict is not None:
                raise DuplicateEntityException(
                    entity_type=USER_ENTITY,
                    description=f"Email '{user.email}' is already taken by another user",
                )

        try:
            async with self._session.begin_nested():
                existing.email = user.email
                existing.username = user.username
                existing.status = user.status
                existing.roles = [r.value for r in user.roles]
                existing.updated_at = _now()
                await self._session.flush()
        except IntegrityError as exc:
            raise DuplicateEntityException(
                entity_type=USER_ENTITY,
                description=f"Email '{user.email}' is already taken by another user",
            ) from exc

        return _to_domain(existing)

    async def delete_user(
        self,
        user_id: uuid.UUID,
        hard_delete: bool = False,
    ) -> None:
        if hard_delete:
            stmt = delete(DBUserProfile).where(DBUserProfile.user_id == user_id)
        else:
            stmt = (
                update(DBUserProfile)
                .where(DBUserProfile.user_id == user_id)
                .values(status=UserStatus.DELETED, updated_at=_now())
            )
        await self._session.execute(stmt)

    async def list_users(self) -> list[UserProfile]:
        stmt = select(DBUserProfile)
        result = await self._session.execute(stmt)
        return [_to_domain(row) for row in result.scalars().all()]
