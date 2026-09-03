import uuid

from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.fastapi_auth_lib.core.constants import AUTH_IDENTITY_ENTITY
from src.fastapi_auth_lib.core.exceptions import DuplicateEntityException
from src.fastapi_auth_lib.core.utils import _now
from src.fastapi_auth_lib.models.auth_identity import AuthIdentity
from src.fastapi_auth_lib.models.base import AuthProvider
from src.fastapi_auth_lib.repositories.async_auth_identity import AsyncAuthIdentityRepository
from src.fastapi_auth_lib.repositories.db_models.db_auth_identity import DBAuthIdentity


def _to_domain(row: DBAuthIdentity) -> AuthIdentity:
    """Map a DB row to the domain model."""
    return AuthIdentity(
        auth_identity_id=row.id,
        user_id=row.user_id,
        provider=AuthProvider(row.provider),
        provider_subject=row.provider_subject,
        password_hash=row.password_hash,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAsyncAuthIdentityRepository(AsyncAuthIdentityRepository):
    """
    SQLAlchemy async implementation of AsyncAuthIdentityRepository.

    Contract:
    - The session is injected and owned by the caller.
    - This repository flushes but NEVER commits.
    - provider_subject must already be normalized by the caller.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_auth_identity(
        self, auth_identity: AuthIdentity
    ) -> AuthIdentity:
        db_identity = DBAuthIdentity(
            user_id=auth_identity.user_id,
            provider=auth_identity.provider,
            provider_subject=auth_identity.provider_subject,
            password_hash=auth_identity.password_hash,
            created_at=auth_identity.created_at,
            updated_at=None,
        )
        if auth_identity.auth_identity_id is not None:
            db_identity.id = auth_identity.auth_identity_id

        try:
            async with self._session.begin_nested():
                self._session.add(db_identity)
                await self._session.flush()
        except IntegrityError as exc:
            raise await self._classify_duplicate(
                auth_identity.provider,
                auth_identity.provider_subject,
                auth_identity.user_id,
            ) from exc

        return _to_domain(db_identity)

    async def find_auth_identity_by_id(
        self, auth_identity_id: int
    ) -> AuthIdentity | None:
        row = await self._session.get(DBAuthIdentity, auth_identity_id)
        return _to_domain(row) if row is not None else None

    async def find_auth_identity_by_user_id(
        self, user_id: uuid.UUID
    ) -> AuthIdentity | None:
        stmt = select(DBAuthIdentity).where(DBAuthIdentity.user_id == user_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _to_domain(row) if row is not None else None

    async def find_auth_identity_by_provider_subject(
        self,
        provider: AuthProvider,
        provider_subject: str,
    ) -> AuthIdentity | None:
        stmt = select(DBAuthIdentity).where(
            DBAuthIdentity.provider == provider,
            DBAuthIdentity.provider_subject == provider_subject,
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _to_domain(row) if row is not None else None

    async def update_auth_identity(
        self,
        auth_identity_id: int,
        auth_identity: AuthIdentity,
    ) -> AuthIdentity | None:
        existing = await self._session.get(DBAuthIdentity, auth_identity_id)
        if existing is None:
            return None

        subject_changed = (
            auth_identity.provider != existing.provider
            or auth_identity.provider_subject != existing.provider_subject
        )
        if subject_changed:
            stmt = select(DBAuthIdentity.id).where(
                DBAuthIdentity.provider == auth_identity.provider,
                DBAuthIdentity.provider_subject == auth_identity.provider_subject,
                DBAuthIdentity.id != auth_identity_id,
            )
            if (await self._session.execute(stmt)).scalar_one_or_none() is not None:
                raise DuplicateEntityException(
                    entity_type=AUTH_IDENTITY_ENTITY,
                    description=(
                        f"An identity for provider '{auth_identity.provider}' "
                        f"with this subject already exists"
                    ),
                )

        if auth_identity.user_id != existing.user_id:
            stmt = select(DBAuthIdentity.id).where(
                DBAuthIdentity.user_id == auth_identity.user_id
            )
            if (await self._session.execute(stmt)).scalar_one_or_none() is not None:
                raise DuplicateEntityException(
                    entity_type=AUTH_IDENTITY_ENTITY,
                    description="The target user already has an authentication identity",
                )

        try:
            async with self._session.begin_nested():
                existing.provider = auth_identity.provider
                existing.provider_subject = auth_identity.provider_subject
                existing.password_hash = auth_identity.password_hash
                existing.user_id = auth_identity.user_id
                existing.updated_at = _now()
                await self._session.flush()
        except IntegrityError as exc:
            raise await self._classify_duplicate(
                auth_identity.provider,
                auth_identity.provider_subject,
                auth_identity.user_id,
            ) from exc

        return _to_domain(existing)

    async def delete_auth_identity(self, auth_identity_id: int) -> None:
        stmt = delete(DBAuthIdentity).where(DBAuthIdentity.id == auth_identity_id)
        await self._session.execute(stmt)

    async def _classify_duplicate(
        self,
        provider: AuthProvider,
        subject: str,
        user_id: uuid.UUID,
    ) -> DuplicateEntityException:
        stmt = select(DBAuthIdentity.id).where(
            DBAuthIdentity.provider == provider,
            DBAuthIdentity.provider_subject == subject,
        )
        if (await self._session.execute(stmt)).scalar_one_or_none() is not None:
            return DuplicateEntityException(
                entity_type=AUTH_IDENTITY_ENTITY,
                description=(
                    f"An identity for provider '{provider}' "
                    f"with this subject already exists"
                ),
            )
        return DuplicateEntityException(
            entity_type=AUTH_IDENTITY_ENTITY,
            description="This user already has an authentication identity",
        )
