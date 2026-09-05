import uuid
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum

import jwt

from src.fastapi_auth_lib.core.exceptions import TokenException
from src.fastapi_auth_lib.core.utils import _now

DEFAULT_ACCESS_TTL = timedelta(minutes=15)
DEFAULT_REFRESH_TTL = timedelta(days=7)
DEFAULT_ACTIVATION_TTL = timedelta(hours=24)


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"
    ACTIVATION = "activation"


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str


class JwtTokenService:
    """
    PyJWT-based token service.

    Security invariants:
    - Every token carries a `type` claim; verification REJECTS tokens whose
      type doesn't match the expected one (an activation token can never be
      used as an access token).
    - The algorithm is pinned; PyJWT's decode never accepts "none" or an
      algorithm the caller didn't configure.
    - PyJWT exceptions are translated into TokenException.
    """

    def __init__(
        self,
        secret: str,
        issuer: str,
        algorithm: str = "HS256",
        access_ttl: timedelta = DEFAULT_ACCESS_TTL,
        refresh_ttl: timedelta = DEFAULT_REFRESH_TTL,
        activation_ttl: timedelta = DEFAULT_ACTIVATION_TTL,
    ) -> None:
        if not secret:
            raise ValueError("JWT secret cannot be empty")
        self._secret = secret
        self._issuer = issuer
        self._algorithm = algorithm
        self._access_ttl = access_ttl
        self._refresh_ttl = refresh_ttl
        self._activation_ttl = activation_ttl

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------
    def create_access_token(self, user_id: uuid.UUID) -> str:
        return self._create_token(user_id, TokenType.ACCESS, self._access_ttl)

    def create_refresh_token(self, user_id: uuid.UUID) -> str:
        return self._create_token(user_id, TokenType.REFRESH, self._refresh_ttl)

    def create_activation_token(self, user_id: uuid.UUID) -> str:
        return self._create_token(user_id, TokenType.ACTIVATION, self._activation_ttl)

    def _create_token(
        self, user_id: uuid.UUID, token_type: TokenType, ttl: timedelta
    ) -> str:
        now = _now()
        payload = {
            "sub": str(user_id),
            "type": token_type.value,
            "iss": self._issuer,
            "iat": now,
            "exp": now + ttl,
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    # ------------------------------------------------------------------
    # Verification — each method enforces its own token type
    # ------------------------------------------------------------------
    def verify_access_token(self, token: str) -> uuid.UUID:
        return self._verify(token, TokenType.ACCESS)

    def verify_refresh_token(self, token: str) -> uuid.UUID:
        return self._verify(token, TokenType.REFRESH)

    def verify_activation_token(self, token: str) -> uuid.UUID:
        return self._verify(token, TokenType.ACTIVATION)

    def _verify(self, token: str, expected_type: TokenType) -> uuid.UUID:
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
                issuer=self._issuer,
            )
        except jwt.ExpiredSignatureError as exc:
            raise TokenException(f"{expected_type.value} token has expired") from exc
        except jwt.InvalidTokenError as exc:
            raise TokenException(f"Invalid {expected_type.value} token") from exc

        if claims.get("type") != expected_type.value:
            raise TokenException(
                f"Token of type '{claims.get('type')}' cannot be used "
                f"as a {expected_type.value} token"
            )
        try:
            return uuid.UUID(claims["sub"])
        except (KeyError, ValueError) as exc:
            raise TokenException("Token subject is missing or malformed") from exc
