import logging

from fastapi_auth_lib.core.logging_config import configure_logging

logger = logging.getLogger(__name__)

# with default settings
configure_logging()

if __name__ == '__main__':
    logger.info("hello info logging!")

    # output without configure_logging:
    # INFO:__main__:hello info logging!

    # output:
    # 2026-08-16 18:56:50 | INFO     | __main__:10 | hello info logging!
