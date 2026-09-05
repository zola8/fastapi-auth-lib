from src.fastapi_auth_lib.core.exceptions import AuthenticationException
from src.fastapi_auth_lib.core.exceptions import DuplicateEntityException
from src.fastapi_auth_lib.core.exceptions import EntityNotFoundException
from src.fastapi_auth_lib.core.exceptions import FeatureNotConfiguredException
from src.fastapi_auth_lib.core.exceptions import TokenException


class TestEntityNotFoundException:
    """Tests for EntityNotFoundException."""

    def test_inherits_from_exception(self):
        """Should be a subclass of Exception."""
        assert issubclass(EntityNotFoundException, Exception)

    def test_message_format(self):
        """Message should combine entity_type and description."""
        exc = EntityNotFoundException("User", "not found")
        assert str(exc) == "User: not found"

    def test_attributes(self):
        """Attributes entity_type and description should be set."""
        exc = EntityNotFoundException("Item", "missing")
        assert exc.entity_type == "Item"
        assert exc.description == "missing"

    def test_none_values(self):
        """None values should be accepted and formatted as 'None'."""
        exc = EntityNotFoundException(None, None)
        assert str(exc) == "None: None"
        assert exc.entity_type is None
        assert exc.description is None

    def test_empty_strings(self):
        """Empty strings produce a message with just a colon."""
        exc = EntityNotFoundException("", "")
        assert str(exc) == ": "


class TestDuplicateEntityException:
    """Tests for DuplicateEntityException."""

    def test_inherits_from_exception(self):
        assert issubclass(DuplicateEntityException, Exception)

    def test_message_format(self):
        exc = DuplicateEntityException("User", "email already exists")
        assert str(exc) == "User: email already exists"

    def test_attributes(self):
        exc = DuplicateEntityException("Product", "duplicate SKU")
        assert exc.entity_type == "Product"
        assert exc.description == "duplicate SKU"

    def test_none_values(self):
        exc = DuplicateEntityException(None, None)
        assert str(exc) == "None: None"
        assert exc.entity_type is None
        assert exc.description is None


class TestAuthenticationException:
    """Tests for AuthenticationException."""

    def test_inherits_from_exception(self):
        assert issubclass(AuthenticationException, Exception)

    def test_message_is_description(self):
        exc = AuthenticationException("Invalid credentials")
        assert str(exc) == "Invalid credentials"

    def test_description_attribute(self):
        exc = AuthenticationException("Wrong password")
        assert exc.description == "Wrong password"

    def test_none_description(self):
        exc = AuthenticationException(None)
        assert str(exc) == "None"
        assert exc.description is None

    def test_empty_description(self):
        exc = AuthenticationException("")
        assert str(exc) == ""


class TestTokenException:
    """Tests for TokenException."""

    def test_inherits_from_exception(self):
        assert issubclass(TokenException, Exception)

    def test_message_is_description(self):
        exc = TokenException("Token expired")
        assert str(exc) == "Token expired"

    def test_description_attribute(self):
        exc = TokenException("Invalid token type")
        assert exc.description == "Invalid token type"

    def test_none_description(self):
        exc = TokenException(None)
        assert str(exc) == "None"
        assert exc.description is None


class TestFeatureNotConfiguredException:
    """Tests for FeatureNotConfiguredException."""

    def test_inherits_from_exception(self):
        assert issubclass(FeatureNotConfiguredException, Exception)

    def test_message_is_description(self):
        exc = FeatureNotConfiguredException("JWT secret not set")
        assert str(exc) == "JWT secret not set"

    def test_description_attribute(self):
        exc = FeatureNotConfiguredException("SMTP disabled")
        assert exc.description == "SMTP disabled"

    def test_none_description(self):
        exc = FeatureNotConfiguredException(None)
        assert str(exc) == "None"
        assert exc.description is None
