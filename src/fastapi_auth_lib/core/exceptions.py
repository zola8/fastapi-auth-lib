class EntityNotFoundException(Exception):
    """Raised when an entity cannot be found by a specific field."""

    def __init__(self, field: str, value, entity_type: str = "Entity"):
        self.field = field
        self.value = value
        self.entity_type = entity_type
        super().__init__(f"{entity_type} not found with {field}={value!r}")


class DuplicateEntityException(Exception):
    """Raised when attempting to create an entity that already exists."""

    def __init__(self, field: str, value, entity_type: str = "Entity"):
        self.field = field
        self.value = value
        self.entity_type = entity_type
        super().__init__(f"{entity_type} already exists with {field}={value!r}")
