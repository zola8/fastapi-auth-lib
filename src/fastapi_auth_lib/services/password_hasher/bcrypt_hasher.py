import logging

import bcrypt

MIN_ROUNDS = 4
DEFAULT_ROUNDS = 12
MAX_ROUNDS = 31
MAX_PASSWORD_BYTES = 72

logger = logging.getLogger(__name__)


class BCryptPasswordHasher:
    """
    bcrypt password hasher.
    """

    def __init__(
        self,
        rounds: int = DEFAULT_ROUNDS,
    ) -> None:
        if not MIN_ROUNDS <= rounds <= MAX_ROUNDS:
            raise ValueError(
                f"bcrypt rounds must be between {MIN_ROUNDS} and {MAX_ROUNDS}"
            )
        self._rounds = rounds

    @staticmethod
    def _secure_password(password: str) -> bytes:
        """Apply salt via HMAC-SHA256 if configured, then encode."""
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > MAX_PASSWORD_BYTES:
            raise ValueError(
                f"Password exceeds bcrypt max length of {MAX_PASSWORD_BYTES} bytes"
            )
        return password_bytes

    def hash_password(self, password: str) -> str:
        if not password:
            raise ValueError("Password cannot be empty")
        secured = self._secure_password(password)
        salt = bcrypt.gensalt(rounds=self._rounds)
        return bcrypt.hashpw(secured, salt).decode("utf-8")

    def verify_password(self, password: str, hashed_password: str) -> bool:
        if not password or not hashed_password:
            return False
        try:
            secured = self._secure_password(password)
            return bcrypt.checkpw(secured, hashed_password.encode("utf-8"))
        except (ValueError, TypeError):
            logger.warning("Password verification failed: malformed bcrypt hash")
            return False
