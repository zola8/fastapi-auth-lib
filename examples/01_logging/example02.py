import logging

from src.fastapi_auth_lib.core.logging_config import LogFormat
from src.fastapi_auth_lib.core.logging_config import configure_logging

logger = logging.getLogger(__name__)

configure_logging(log_format=LogFormat.PROD)

if __name__ == '__main__':
    logger.info("hello info logging!")

    # output:
    # {"asctime": "2026-08-17 08:31:36,769", "levelname": "INFO", "name": "__main__", "message": "hello info logging!"}
