import uuid

from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.fastapi_auth_lib.models.refresh_token import RefreshToken
from src.fastapi_auth_lib.repositories.async_refresh_token import AsyncRefreshTokenRepository
from src.fastapi_auth_lib.repositories.db_models.db_refresh_token import DBRefreshToken


def _to_domain(row: DBRefreshToken) -> RefreshToken:
    return RefreshToken(
        refresh_token_id=row.id,
        user_id=row.user_id,
        token_hash=row.token_hash,
        created_at=row.created_at,
        expires_at=row.expires_at,
    )


class SqlAsyncRefreshTokenRepository(AsyncRefreshTokenRepository):
    """
    Contract:
     - Session injected and owned by the caller.
     - Flushes but NEVER commits.
     - token_hash must already be computed by the service layer.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_refresh_token(self, token: RefreshToken) -> RefreshToken:
        db_token = DBRefreshToken(
            user_id=token.user_id,
            token_hash=token.token_hash,
            expires_at=token.expires_at,
        )
        self._session.add(db_token)
        await self._session.flush()
        return _to_domain(db_token)

    async def find_refresh_token_by_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(DBRefreshToken).where(DBRefreshToken.token_hash == token_hash)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row is not None else None

    async def delete_refresh_token(self, refresh_token_id: int) -> None:
        stmt = delete(DBRefreshToken).where(DBRefreshToken.id == refresh_token_id)
        await self._session.execute(stmt)  # no-op if missing — idempotent

    async def delete_all_for_user(self, user_id: uuid.UUID) -> None:
        stmt = delete(DBRefreshToken).where(DBRefreshToken.user_id == user_id)
        await self._session.execute(stmt)
