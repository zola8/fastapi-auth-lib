class EntityNotFoundException(Exception):
    """Raised by the service layer when a required entity does not exist."""

    def __init__(self, entity_type: str, description: str) -> None:
        self.entity_type = entity_type
        self.description = description
        super().__init__(f"{entity_type}: {description}")


class DuplicateEntityException(Exception):
    """Raised by the repository layer when a uniqueness constraint is violated."""

    def __init__(self, entity_type: str, description: str) -> None:
        self.entity_type = entity_type
        self.description = description
        super().__init__(f"{entity_type}: {description}")


class AuthenticationException(Exception):
    """Raised when credentials are invalid during login."""

    def __init__(self, description: str) -> None:
        self.description = description
        super().__init__(description)


class TokenException(Exception):
    """Raised when a token is invalid, expired, or of the wrong type."""

    def __init__(self, description: str) -> None:
        self.description = description
        super().__init__(description)


class FeatureNotConfiguredException(Exception):
    """Raised when an optional feature is used but was not configured."""

    def __init__(self, description: str) -> None:
        self.description = description
        super().__init__(description)
