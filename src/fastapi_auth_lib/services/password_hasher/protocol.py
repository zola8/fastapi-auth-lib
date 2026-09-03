from typing import Protocol


class PasswordHasherProtocol(Protocol):
    """Structural contract for password hashers. No inheritance required."""

    def hash_password(self, password: str) -> str:
        """
        Hash a raw password.
        Raises ValueError if the password is invalid.
        """
        ...

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a raw password against a stored hash.
        Returns True if match, False otherwise.
        Never raises on mismatch or malformed hash.
        """
        ...
