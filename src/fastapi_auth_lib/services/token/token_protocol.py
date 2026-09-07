from enum import StrEnum
from typing import Protocol
from uuid import UUID


class TokenType(StrEnum):
    ACTIVATION = "activation"
    PASSWORD_RESET = "password_reset"
    ACCESS = "access"
    REFRESH = "refresh"


class TokenServiceProtocol(Protocol):
    """Contract for token engines. Verification always returns the user_id."""

    def create_activation_token(self, user_id: UUID) -> str: ...

    def create_access_token(self, user_id: UUID) -> str: ...

    def create_refresh_token(self, user_id: UUID) -> str: ...

    def verify_activation_token(self, token: str) -> UUID: ...

    def verify_access_token(self, token: str) -> UUID: ...

    def verify_refresh_token(self, token: str) -> UUID: ...

    def create_reset_token(self, user_id: UUID) -> str: ...

    def verify_reset_token(self, token: str) -> UUID: ...
