import uuid
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import jwt
import pytest

from src.fastapi_auth_lib.core.exceptions import TokenException
from src.fastapi_auth_lib.services.token.jwt_token_service import DEFAULT_ACCESS_TTL
from src.fastapi_auth_lib.services.token.jwt_token_service import DEFAULT_ACTIVATION_TTL
from src.fastapi_auth_lib.services.token.jwt_token_service import DEFAULT_REFRESH_TTL
from src.fastapi_auth_lib.services.token.jwt_token_service import JwtTokenService
from src.fastapi_auth_lib.services.token.jwt_token_service import TokenType

TEST_SECRET = "test-secret-which-is-long-enough"
TEST_ISSUER = "test-issuer"


class TestJwtTokenServiceConstructor:
    """Tests for __init__ and parameter validation."""

    def test_valid_construction(self):
        """Should create instance with default algorithm and TTLs."""
        service = JwtTokenService(secret=TEST_SECRET, issuer=TEST_ISSUER)
        assert service._secret == TEST_SECRET
        assert service._issuer == TEST_ISSUER
        assert service._algorithm == "HS256"
        assert service._access_ttl == DEFAULT_ACCESS_TTL
        assert service._refresh_ttl == DEFAULT_REFRESH_TTL
        assert service._activation_ttl == DEFAULT_ACTIVATION_TTL

    def test_custom_values(self):
        """Should accept custom TTLs and algorithm."""
        service = JwtTokenService(
            secret=TEST_SECRET,
            issuer="issuer",
            algorithm="HS384",
            access_ttl=timedelta(minutes=30),
            refresh_ttl=timedelta(days=14),
            activation_ttl=timedelta(hours=48),
        )
        assert service._algorithm == "HS384"
        assert service._access_ttl == timedelta(minutes=30)
        assert service._refresh_ttl == timedelta(days=14)
        assert service._activation_ttl == timedelta(hours=48)

    def test_empty_secret_raises(self):
        """Empty secret should raise ValueError."""
        with pytest.raises(ValueError):
            JwtTokenService(secret="", issuer="issuer")

    def test_none_secret_raises(self):
        """None secret should raise ValueError (or TypeError)."""
        with pytest.raises((ValueError, TypeError)):
            JwtTokenService(secret=None, issuer="issuer")


class TestJwtTokenServiceCreation:
    """Tests for token creation methods."""

    def setup_method(self):
        self.service = JwtTokenService(secret=TEST_SECRET, issuer=TEST_ISSUER)
        self.user_id = uuid.uuid4()

    def decode_token(self, token: str) -> dict:
        """Decode a token without verification to inspect claims."""
        return jwt.decode(
            token,
            TEST_SECRET,
            algorithms=["HS256"],
            issuer=TEST_ISSUER,
        )

    def test_create_access_token(self):
        """Access token should contain correct type and sub."""
        token = self.service.create_access_token(self.user_id)
        claims = self.decode_token(token)
        assert claims["sub"] == str(self.user_id)
        assert claims["type"] == TokenType.ACCESS.value
        assert claims["iss"] == TEST_ISSUER
        assert "iat" in claims
        assert "exp" in claims

    def test_create_refresh_token(self):
        """Refresh token should have type=refresh."""
        token = self.service.create_refresh_token(self.user_id)
        claims = self.decode_token(token)
        assert claims["type"] == TokenType.REFRESH.value

    def test_create_activation_token(self):
        """Activation token should have type=activation."""
        token = self.service.create_activation_token(self.user_id)
        claims = self.decode_token(token)
        assert claims["type"] == TokenType.ACTIVATION.value

    def test_token_expiry_within_ttl(self):
        """exp should be approximately now + TTL."""
        token = self.service.create_access_token(self.user_id)
        claims = self.decode_token(token)

        exp = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
        expected_exp = datetime.now(timezone.utc) + DEFAULT_ACCESS_TTL

        # Allow up to 5 seconds slack for execution time
        assert abs((exp - expected_exp).total_seconds()) < 5


class TestJwtTokenServiceVerification:
    """Tests for verification methods."""

    def setup_method(self):
        self.service = JwtTokenService(secret=TEST_SECRET, issuer=TEST_ISSUER)
        self.user_id = uuid.uuid4()

    def test_verify_access_token_success(self):
        """Should return user_id for valid access token."""
        token = self.service.create_access_token(self.user_id)
        assert self.service.verify_access_token(token) == self.user_id

    def test_verify_refresh_token_success(self):
        token = self.service.create_refresh_token(self.user_id)
        assert self.service.verify_refresh_token(token) == self.user_id

    def test_verify_activation_token_success(self):
        token = self.service.create_activation_token(self.user_id)
        assert self.service.verify_activation_token(token) == self.user_id

    def test_wrong_token_type_raises(self):
        """An access token used as refresh should raise TokenException."""
        access_token = self.service.create_access_token(self.user_id)
        with pytest.raises(TokenException) as exc_info:
            self.service.verify_refresh_token(access_token)
        assert "cannot be used" in str(exc_info.value)

    def test_expired_token_raises(self):
        """Expired token should raise TokenException."""
        service = JwtTokenService(
            secret=TEST_SECRET,
            issuer=TEST_ISSUER,
            access_ttl=timedelta(seconds=-1),  # already expired
        )
        token = service.create_access_token(self.user_id)
        with pytest.raises(TokenException) as exc_info:
            service.verify_access_token(token)
        assert "expired" in str(exc_info.value).lower()

    def test_invalid_signature_raises(self):
        """Token signed with wrong secret should raise TokenException."""
        service = JwtTokenService(secret=TEST_SECRET, issuer=TEST_ISSUER)
        token = service.create_access_token(self.user_id)
        # tamper with signature
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        with pytest.raises(TokenException) as exc_info:
            service.verify_access_token(tampered)
        assert "invalid" in str(exc_info.value).lower()

    def test_missing_type_claim_raises(self):
        """Token without type claim should raise TokenException."""
        service = JwtTokenService(secret=TEST_SECRET, issuer=TEST_ISSUER)
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(self.user_id),
            "iss": TEST_ISSUER,
            "iat": now,
            "exp": now + timedelta(minutes=5),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")
        with pytest.raises(TokenException):
            service.verify_access_token(token)

    def test_wrong_type_claim_raises(self):
        """Token with wrong type claim should raise TokenException."""
        service = JwtTokenService(secret=TEST_SECRET, issuer=TEST_ISSUER)
        # create a refresh token, but try to verify as access
        refresh_token = service.create_refresh_token(self.user_id)
        with pytest.raises(TokenException):
            service.verify_access_token(refresh_token)

    def test_missing_sub_claim_raises(self):
        """Token without sub claim should raise TokenException."""
        service = JwtTokenService(secret=TEST_SECRET, issuer=TEST_ISSUER)
        now = datetime.now(timezone.utc)
        payload = {
            "type": TokenType.ACCESS.value,
            "iss": TEST_ISSUER,
            "iat": now,
            "exp": now + timedelta(minutes=5),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")
        with pytest.raises(TokenException):
            service.verify_access_token(token)

    def test_malformed_sub_raises(self):
        """Token with non-UUID sub should raise TokenException."""
        service = JwtTokenService(secret=TEST_SECRET, issuer=TEST_ISSUER)
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "not-a-uuid",
            "type": TokenType.ACCESS.value,
            "iss": TEST_ISSUER,
            "iat": now,
            "exp": now + timedelta(minutes=5),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")
        with pytest.raises(TokenException):
            service.verify_access_token(token)

    def test_verify_none_token_raises(self):
        """None token should raise TokenException (from jwt.InvalidTokenError)."""
        with pytest.raises(TokenException):
            self.service.verify_access_token(None)

    def test_verify_empty_string_raises(self):
        """Empty token should raise TokenException."""
        with pytest.raises(TokenException):
            self.service.verify_access_token("")
