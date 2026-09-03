import logging

from argon2 import PasswordHasher as Argon2LibHasher
from argon2.exceptions import InvalidHashError
from argon2.exceptions import VerificationError
from argon2.exceptions import VerifyMismatchError

logger = logging.getLogger(__name__)

# Argon2 RFC recommendations
DEFAULT_TIME_COST = 3
DEFAULT_MEMORY_COST = 65536
DEFAULT_PARALLELISM = 4


class Argon2PasswordHasher:
    """
    Argon2id password hasher with optional pepper support.
    """

    def __init__(
        self,
        time_cost: int = DEFAULT_TIME_COST,
        memory_cost: int = DEFAULT_MEMORY_COST,
        parallelism: int = DEFAULT_PARALLELISM,
    ) -> None:
        self._hasher = Argon2LibHasher(
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism,
        )

    def hash_password(self, password: str) -> str:
        if not password:
            raise ValueError("Password cannot be empty")
        return self._hasher.hash(password)

    def verify_password(self, password: str, hashed_password: str) -> bool:
        if not password or not hashed_password:
            return False
        try:
            self._hasher.verify(hashed_password, password)
            return True
        except VerifyMismatchError:
            logger.warning("Password verification failed: Argon2id mismatch")
            return False
        except (InvalidHashError, VerificationError):
            logger.warning("Password verification failed: malformed Argon2id hash")
            return False
