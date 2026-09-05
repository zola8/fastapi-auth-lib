import logging

logger = logging.getLogger(__name__)


class DummyLoggerEmailService:
    """
    Development/testing email service.

    Sends nothing — logs the email that would have been sent.
    """

    @staticmethod
    async def send_email(to: str, subject: str, body: str) -> None:
        logger.info(
            "DummyEmail | to: %s | subject: %s\n--- body ---\n%s\n------------",
            to,
            subject,
            body,
        )
