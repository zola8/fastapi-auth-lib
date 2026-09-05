import pytest

from src.fastapi_auth_lib.services.password_hasher.argon2_hasher import Argon2PasswordHasher
from src.fastapi_auth_lib.services.password_hasher.argon2_hasher import DEFAULT_MEMORY_COST
from src.fastapi_auth_lib.services.password_hasher.argon2_hasher import DEFAULT_PARALLELISM
from src.fastapi_auth_lib.services.password_hasher.argon2_hasher import DEFAULT_TIME_COST


class TestArgon2PasswordHasherConstructor:
    """Tests for __init__ parameter handling."""

    def test_default_parameters(self):
        """Should use library defaults if not specified."""
        hasher = Argon2PasswordHasher()
        assert hasher._hasher.time_cost == DEFAULT_TIME_COST
        assert hasher._hasher.memory_cost == DEFAULT_MEMORY_COST
        assert hasher._hasher.parallelism == DEFAULT_PARALLELISM

    def test_custom_parameters(self):
        """Should accept custom Argon2 parameters."""
        time_cost = 2
        memory_cost = 16
        parallelism = 2
        hasher = Argon2PasswordHasher(
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism,
        )
        assert hasher._hasher.time_cost == time_cost
        assert hasher._hasher.memory_cost == memory_cost
        assert hasher._hasher.parallelism == parallelism


class TestArgon2PasswordHasherHashPassword:
    """Tests for hash_password."""

    def setup_method(self):
        # low cost for fast tests
        self.hasher = Argon2PasswordHasher(
            time_cost=1,
            memory_cost=8,
            parallelism=1,
        )

    def test_hash_password_returns_string(self):
        """Should return a string."""
        hashed = self.hasher.hash_password("secret")
        assert isinstance(hashed, str)

    def test_hash_password_has_argon2_prefix(self):
        """Result should start with $argon2id$."""
        hashed = self.hasher.hash_password("secret")
        assert hashed.startswith("$argon2id$")

    def test_hash_password_same_input_different_salts(self):
        """Two hashes of same password should differ (random salt)."""
        hash1 = self.hasher.hash_password("secret")
        hash2 = self.hasher.hash_password("secret")
        assert hash1 != hash2

    def test_hash_password_empty_string_raises(self):
        """Empty password should raise ValueError."""
        with pytest.raises(ValueError):
            self.hasher.hash_password("")

    def test_hash_password_none_raises(self):
        """None password should raise ValueError."""
        with pytest.raises(ValueError):
            self.hasher.hash_password(None)

    def test_hash_password_unicode(self):
        """Unicode password should be hashed."""
        password = "pässwörd✓"
        hashed = self.hasher.hash_password(password)
        assert isinstance(hashed, str)

    def test_hash_password_long(self):
        """Long password should be accepted."""
        password = "a" * 1000
        hashed = self.hasher.hash_password(password)
        assert isinstance(hashed, str)


class TestArgon2PasswordHasherVerifyPassword:
    """Tests for verify_password."""

    def setup_method(self):
        self.hasher = Argon2PasswordHasher(
            time_cost=1,
            memory_cost=8,
            parallelism=1,
        )

    def test_verify_correct_password(self):
        """Verify should return True for correct password."""
        hashed = self.hasher.hash_password("secret")
        assert self.hasher.verify_password("secret", hashed) is True

    def test_verify_wrong_password(self):
        """Verify should return False for wrong password."""
        hashed = self.hasher.hash_password("secret")
        assert self.hasher.verify_password("wrong", hashed) is False

    def test_verify_none_password(self):
        """Verify should return False for None password."""
        hashed = self.hasher.hash_password("secret")
        assert self.hasher.verify_password(None, hashed) is False

    def test_verify_none_hashed(self):
        """Verify should return False for None hashed_password."""
        assert self.hasher.verify_password("secret", None) is False

    def test_verify_both_none(self):
        """Verify should return False for both None."""
        assert self.hasher.verify_password(None, None) is False

    def test_verify_empty_password(self):
        """Verify should return False for empty password."""
        hashed = self.hasher.hash_password("secret")
        assert self.hasher.verify_password("", hashed) is False

    def test_verify_empty_hashed(self):
        """Verify should return False for empty hashed_password."""
        assert self.hasher.verify_password("secret", "") is False

    def test_verify_malformed_hash(self):
        """Verify should return False for malformed hash and not raise."""
        assert self.hasher.verify_password("secret", "not-a-valid-hash") is False
        assert self.hasher.verify_password("secret", "123") is False

    def test_verify_roundtrip_unicode(self):
        """Hash and verify should work with unicode."""
        password = "pässwörd✓"
        hashed = self.hasher.hash_password(password)
        assert self.hasher.verify_password(password, hashed) is True
