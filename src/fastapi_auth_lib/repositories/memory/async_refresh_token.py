from uuid import UUID

from src.fastapi_auth_lib.models.refresh_token import RefreshToken
from src.fastapi_auth_lib.repositories.async_refresh_token import AsyncRefreshTokenRepository


class InMemoryAsyncRefreshTokenRepository(AsyncRefreshTokenRepository):
    def __init__(self) -> None:
        self._tokens: dict[int, RefreshToken] = {}
        self._next_id = 1

    async def create_refresh_token(self, token: RefreshToken) -> RefreshToken:
        stored = token.model_copy(deep=True)
        stored.refresh_token_id = self._next_id
        self._next_id += 1
        self._tokens[stored.refresh_token_id] = stored
        return stored.model_copy(deep=True)

    async def find_refresh_token_by_hash(self, token_hash: str) -> RefreshToken | None:
        for token in self._tokens.values():
            if token.token_hash == token_hash:
                return token.model_copy(deep=True)
        return None

    async def delete_refresh_token(self, refresh_token_id: int) -> None:
        self._tokens.pop(refresh_token_id, None)  # idempotent

    async def delete_all_for_user(self, user_id: UUID) -> None:
        stale = [
            tid for tid, t in self._tokens.items() if t.user_id == user_id
        ]
        for tid in stale:
            del self._tokens[tid]
