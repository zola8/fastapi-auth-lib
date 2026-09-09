from abc import ABC
from abc import abstractmethod
from uuid import UUID

from src.fastapi_auth_lib.models.refresh_token import RefreshToken


class AsyncRefreshTokenRepository(ABC):
    """Contract for refresh token (session) storage."""

    @abstractmethod
    async def create_refresh_token(self, token: RefreshToken) -> RefreshToken: ...

    @abstractmethod
    async def find_refresh_token_by_hash(self, token_hash: str) -> RefreshToken | None: ...

    @abstractmethod
    async def delete_refresh_token(self, refresh_token_id: int) -> None: ...

    @abstractmethod
    async def delete_all_for_user(self, user_id: UUID) -> None: ...
