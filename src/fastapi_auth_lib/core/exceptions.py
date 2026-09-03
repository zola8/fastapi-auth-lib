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
