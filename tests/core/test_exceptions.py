import pytest

from fastapi_auth_lib.core.exceptions import DuplicateEntityException
from fastapi_auth_lib.core.exceptions import EntityNotFoundException


class TestEntityNotFoundException:
    def test_entity_not_found_with_id(self):
        exc = EntityNotFoundException(field="id", value=123, entity_type="User")

        assert exc.field == "id"
        assert exc.value == 123
        assert exc.entity_type == "User"
        assert str(exc) == "User not found with id=123"

    def test_entity_not_found_with_email(self):
        exc = EntityNotFoundException(
            field="email",
            value="user@example.com",
            entity_type="User",
        )

        assert exc.field == "email"
        assert exc.value == "user@example.com"
        assert exc.entity_type == "User"
        assert str(exc) == "User not found with email='user@example.com'"

    def test_entity_not_found_default_entity_type(self):
        exc = EntityNotFoundException(field="id", value=999)

        assert exc.field == "id"
        assert exc.value == 999
        assert exc.entity_type == "Entity"
        assert str(exc) == "Entity not found with id=999"

    def test_entity_not_found_can_be_raised_and_caught(self):
        with pytest.raises(EntityNotFoundException) as exc_info:
            raise EntityNotFoundException(
                field="email",
                value="missing@example.com",
                entity_type="User",
            )

        exc = exc_info.value
        assert exc.field == "email"
        assert exc.value == "missing@example.com"
        assert exc.entity_type == "User"

    def test_entity_not_found_is_exception(self):
        assert issubclass(EntityNotFoundException, Exception)


class TestDuplicateEntityException:
    def test_duplicate_entity_with_email(self):
        exc = DuplicateEntityException(
            field="email",
            value="user@example.com",
            entity_type="User",
        )

        assert exc.field == "email"
        assert exc.value == "user@example.com"
        assert exc.entity_type == "User"
        assert str(exc) == "User already exists with email='user@example.com'"

    def test_duplicate_entity_with_id(self):
        exc = DuplicateEntityException(
            field="id",
            value=42,
            entity_type="Order",
        )

        assert exc.field == "id"
        assert exc.value == 42
        assert exc.entity_type == "Order"
        assert str(exc) == "Order already exists with id=42"

    def test_duplicate_entity_default_entity_type(self):
        exc = DuplicateEntityException(field="username", value="dummy_user")

        assert exc.field == "username"
        assert exc.value == "dummy_user"
        assert exc.entity_type == "Entity"
        assert str(exc) == "Entity already exists with username='dummy_user'"

    def test_duplicate_entity_can_be_raised_and_caught(self):
        with pytest.raises(DuplicateEntityException) as exc_info:
            raise DuplicateEntityException(
                field="email",
                value="duplicate@example.com",
                entity_type="User",
            )

        exc = exc_info.value
        assert exc.field == "email"
        assert exc.value == "duplicate@example.com"
        assert exc.entity_type == "User"

    def test_duplicate_entity_is_exception(self):
        assert issubclass(DuplicateEntityException, Exception)
