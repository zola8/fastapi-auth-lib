import logging

logger = logging.getLogger(__name__)


class PlaintextHasher:
    """
    Identity "hasher": stores the password unchanged.

    WARNING: For tests, demos and local scripts ONLY. Never use in production.
    """

    def __init__(self) -> None:
        logger.warning(
            "PlaintextHasher in use — passwords are stored unhashed. "
            "Never use this in production."
        )

    @staticmethod
    def hash_password(password: str) -> str:
        if password is None or password == "":
            raise ValueError("Password cannot be None or empty")
        return password

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        if not password or not hashed_password:
            return False
        return password == hashed_password
