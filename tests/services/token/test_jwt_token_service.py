import uuid
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import jwt
import pytest

from src.fastapi_auth_lib.core.exceptions import TokenException
from src.fastapi_auth_lib.core.utils import _now
from src.fastapi_auth_lib.services.token.jwt_token_service import DEFAULT_ACCESS_TTL
from src.fastapi_auth_lib.services.token.jwt_token_service import DEFAULT_ACTIVATION_TTL
from src.fastapi_auth_lib.services.token.jwt_token_service import DEFAULT_REFRESH_TTL
from src.fastapi_auth_lib.services.token.jwt_token_service import DEFAULT_RESET_TTL
from src.fastapi_auth_lib.services.token.jwt_token_service import JwtTokenService
from src.fastapi_auth_lib.services.token.jwt_token_service import TokenType
from tests.conftest import TEST_ISSUER
from tests.conftest import TEST_SECRET


class TestJwtTokenServiceConstructor:
    """Tests for __init__ and parameter validation."""

    def test_valid_construction(self, token_service):
        """Should use defaults when not specified."""
        assert token_service._secret == TEST_SECRET
        assert token_service._issuer == TEST_ISSUER
        assert token_service._algorithm == "HS256"
        assert token_service._access_ttl == DEFAULT_ACCESS_TTL
        assert token_service._refresh_ttl == DEFAULT_REFRESH_TTL
        assert token_service._activation_ttl == DEFAULT_ACTIVATION_TTL
        assert token_service._reset_ttl == DEFAULT_RESET_TTL

    def test_custom_values(self):
        """Should accept custom TTLs and algorithm."""
        service = JwtTokenService(
            secret=TEST_SECRET,
            issuer="custom-issuer",
            algorithm="HS384",
            access_ttl=timedelta(minutes=30),
            refresh_ttl=timedelta(days=14),
            activation_ttl=timedelta(hours=48),
            reset_ttl=timedelta(hours=1),
        )
        assert service._algorithm == "HS384"
        assert service._access_ttl == timedelta(minutes=30)
        assert service._refresh_ttl == timedelta(days=14)
        assert service._activation_ttl == timedelta(hours=48)
        assert service._reset_ttl == timedelta(hours=1)

    def test_empty_secret_raises(self):
        """Empty secret should raise ValueError."""
        with pytest.raises(ValueError):
            JwtTokenService(secret="", issuer="issuer")

    def test_none_secret_raises(self):
        """None secret should raise ValueError."""
        with pytest.raises(ValueError):
            JwtTokenService(secret=None, issuer="issuer")


class TestJwtTokenServiceCreation:
    """Tests for token creation methods."""

    def decode_token(self, token: str) -> dict:
        """Decode a token using the known test secret and issuer."""
        return jwt.decode(
            token,
            TEST_SECRET,
            algorithms=["HS256"],
            issuer=TEST_ISSUER,
        )

    def test_create_access_token(self, token_service):
        user_id = uuid.uuid4()
        token = token_service.create_access_token(user_id)
        claims = self.decode_token(token)
        assert claims["sub"] == str(user_id)
        assert claims["type"] == TokenType.ACCESS.value
        assert claims["iss"] == TEST_ISSUER
        assert "iat" in claims
        assert "exp" in claims

    def test_create_refresh_token(self, token_service):
        user_id = uuid.uuid4()
        token = token_service.create_refresh_token(user_id)
        claims = self.decode_token(token)
        assert claims["type"] == TokenType.REFRESH.value

    def test_create_activation_token(self, token_service):
        user_id = uuid.uuid4()
        token = token_service.create_activation_token(user_id)
        claims = self.decode_token(token)
        assert claims["type"] == TokenType.ACTIVATION.value

    def test_create_reset_token(self, token_service):
        user_id = uuid.uuid4()
        token = token_service.create_reset_token(user_id)
        claims = self.decode_token(token)
        assert claims["type"] == TokenType.PASSWORD_RESET.value

    def test_token_expiry_within_ttl(self, token_service):
        user_id = uuid.uuid4()
        token = token_service.create_access_token(user_id)
        claims = self.decode_token(token)

        exp = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
        expected_exp = _now() + DEFAULT_ACCESS_TTL
        # Allow up to 5 seconds slack for execution time
        assert abs((exp - expected_exp).total_seconds()) < 5


class TestJwtTokenServiceVerification:
    """Tests for verification methods."""

    def test_verify_access_token_success(self, token_service):
        user_id = uuid.uuid4()
        token = token_service.create_access_token(user_id)
        assert token_service.verify_access_token(token) == user_id

    def test_verify_refresh_token_success(self, token_service):
        user_id = uuid.uuid4()
        token = token_service.create_refresh_token(user_id)
        assert token_service.verify_refresh_token(token) == user_id

    def test_verify_activation_token_success(self, token_service):
        user_id = uuid.uuid4()
        token = token_service.create_activation_token(user_id)
        assert token_service.verify_activation_token(token) == user_id

    def test_verify_reset_token_success(self, token_service):
        user_id = uuid.uuid4()
        token = token_service.create_reset_token(user_id)
        assert token_service.verify_reset_token(token) == user_id

    def test_wrong_token_type_raises(self, token_service):
        user_id = uuid.uuid4()
        access_token = token_service.create_access_token(user_id)
        with pytest.raises(TokenException) as exc_info:
            token_service.verify_refresh_token(access_token)
        assert "cannot be used" in str(exc_info.value)

    def test_expired_token_raises(self):
        service = JwtTokenService(
            secret=TEST_SECRET,
            issuer=TEST_ISSUER,
            access_ttl=timedelta(seconds=-1),  # already expired
        )
        user_id = uuid.uuid4()
        token = service.create_access_token(user_id)
        with pytest.raises(TokenException) as exc_info:
            service.verify_access_token(token)
        assert "expired" in str(exc_info.value).lower()

    def test_invalid_signature_raises(self, token_service):
        user_id = uuid.uuid4()
        token = token_service.create_access_token(user_id)
        # tamper with signature
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        with pytest.raises(TokenException) as exc_info:
            token_service.verify_access_token(tampered)
        assert "invalid" in str(exc_info.value).lower()

    def test_missing_type_claim_raises(self, token_service):
        user_id = uuid.uuid4()
        now = _now()
        payload = {
            "sub": str(user_id),
            "iss": TEST_ISSUER,
            "iat": now,
            "exp": now + timedelta(minutes=5),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")
        with pytest.raises(TokenException):
            token_service.verify_access_token(token)

    def test_wrong_type_claim_raises(self, token_service):
        user_id = uuid.uuid4()
        refresh_token = token_service.create_refresh_token(user_id)
        with pytest.raises(TokenException):
            token_service.verify_access_token(refresh_token)

    def test_missing_sub_claim_raises(self, token_service):
        now = _now()
        payload = {
            "type": TokenType.ACCESS.value,
            "iss": TEST_ISSUER,
            "iat": now,
            "exp": now + timedelta(minutes=5),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")
        with pytest.raises(TokenException):
            token_service.verify_access_token(token)

    def test_malformed_sub_raises(self, token_service):
        now = _now()
        payload = {
            "sub": "not-a-uuid",
            "type": TokenType.ACCESS.value,
            "iss": TEST_ISSUER,
            "iat": now,
            "exp": now + timedelta(minutes=5),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")
        with pytest.raises(TokenException):
            token_service.verify_access_token(token)

    def test_verify_none_token_raises(self, token_service):
        with pytest.raises(TokenException):
            token_service.verify_access_token(None)

    def test_verify_empty_string_raises(self, token_service):
        with pytest.raises(TokenException):
            token_service.verify_access_token("")
