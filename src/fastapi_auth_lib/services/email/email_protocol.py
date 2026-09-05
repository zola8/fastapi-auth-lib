from typing import Protocol


class EmailServiceProtocol(Protocol):
    """Structural contract for email delivery. No inheritance required."""

    async def send_email(self, to: str, subject: str, body: str) -> None:
        """
        Send an email.

        Async because real implementations perform network I/O (SMTP, API).
        """
        ...
