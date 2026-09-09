import hashlib
from datetime import datetime
from datetime import timezone
from uuid import UUID

import jwt as pyjwt

from src.fastapi_auth_lib.core.exceptions import TokenException
from src.fastapi_auth_lib.models.refresh_token import RefreshToken
from src.fastapi_auth_lib.repositories.async_refresh_token import AsyncRefreshTokenRepository
from src.fastapi_auth_lib.services.token.token_protocol import TokenServiceProtocol


class RefreshTokenService:
    """
    Manages stateful refresh token sessions.

    The refresh token IS a JWT (created by the token service).
    We store its SHA-256 hash so we can revoke it server-side.
    Verification = JWT signature check + DB presence check.
    """

    def __init__(
        self,
        token_service: TokenServiceProtocol,
        refresh_token_repo: AsyncRefreshTokenRepository,
    ) -> None:
        self._token_service = token_service
        self._repo = refresh_token_repo

    async def issue_refresh_token(self, user_id: UUID) -> str:
        """
        Create a refresh token JWT and store its hash.
        Returns the JWT string (sent to the client).
        """
        # The JWT IS the refresh token
        jwt_token = self._token_service.create_refresh_token(user_id)
        token_hash = self._hash(jwt_token)

        # Extract exp claim to store in DB (for cleanup jobs / defense-in-depth)
        payload = pyjwt.decode(jwt_token, options={"verify_signature": False})
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        await self._repo.create_refresh_token(
            RefreshToken(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
        )

        return jwt_token

    async def verify_refresh_token(self, token: str) -> UUID:
        """
        Verify the refresh token:
        1. JWT signature + expiry (via token_service)
        2. Hash exists in DB (not revoked)

        Returns user_id if valid, raises TokenException otherwise.
        """
        # Step 1: Verify JWT signature and expiry
        user_id = self._token_service.verify_refresh_token(token)

        # Step 2: Confirm hash exists in storage (not revoked)
        token_hash = self._hash(token)
        stored = await self._repo.find_refresh_token_by_hash(token_hash)
        if stored is None:
            raise TokenException("Refresh token has been revoked")

        return user_id

    async def revoke_refresh_token(self, token: str) -> None:
        """Revoke a single session. Idempotent."""
        token_hash = self._hash(token)
        stored = await self._repo.find_refresh_token_by_hash(token_hash)
        if stored is not None:
            await self._repo.delete_refresh_token(stored.refresh_token_id)

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        """Revoke all sessions for a user (logout everywhere)."""
        await self._repo.delete_all_for_user(user_id)

    async def rotate_refresh_token(self, old_token: str) -> tuple[UUID, str]:
        """
        Verify old token → revoke it → issue new one.
        Returns (user_id, new_token).
        Provides reuse detection: stolen token used once invalidates the original.
        """
        user_id = await self.verify_refresh_token(old_token)
        await self.revoke_refresh_token(old_token)
        new_token = await self.issue_refresh_token(user_id)
        return user_id, new_token

    @staticmethod
    def _hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
