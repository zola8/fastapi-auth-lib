import pytest

from src.fastapi_auth_lib.services.password_hasher.bcrypt_hasher import BCryptPasswordHasher
from src.fastapi_auth_lib.services.password_hasher.bcrypt_hasher import DEFAULT_ROUNDS
from src.fastapi_auth_lib.services.password_hasher.bcrypt_hasher import MAX_PASSWORD_BYTES
from src.fastapi_auth_lib.services.password_hasher.bcrypt_hasher import MAX_ROUNDS
from src.fastapi_auth_lib.services.password_hasher.bcrypt_hasher import MIN_ROUNDS


class TestBCryptPasswordHasherConstructor:
    """Tests for __init__ and rounds validation."""

    def test_default_rounds(self):
        """Should use DEFAULT_ROUNDS if not specified."""
        hasher = BCryptPasswordHasher()
        assert hasher._rounds == DEFAULT_ROUNDS

    @pytest.mark.parametrize("rounds", [MIN_ROUNDS, 8, MAX_ROUNDS])
    def test_valid_rounds_accepted(self, rounds):
        """Rounds within [MIN_ROUNDS, MAX_ROUNDS] should be accepted."""
        hasher = BCryptPasswordHasher(rounds=rounds)
        assert hasher._rounds == rounds

    def test_rounds_below_min_raises(self):
        """Rounds below MIN_ROUNDS should raise ValueError."""
        with pytest.raises(ValueError):
            BCryptPasswordHasher(rounds=MIN_ROUNDS - 1)

    def test_rounds_above_max_raises(self):
        """Rounds above MAX_ROUNDS should raise ValueError."""
        with pytest.raises(ValueError):
            BCryptPasswordHasher(rounds=MAX_ROUNDS + 1)

    def test_rounds_none_raises(self):
        """None rounds should raise TypeError or ValueError."""
        with pytest.raises((TypeError, ValueError)):
            BCryptPasswordHasher(rounds=None)


class TestBCryptPasswordHasherHashPassword:
    """Tests for hash_password."""

    def setup_method(self):
        # use minimum rounds for speed
        self.hasher = BCryptPasswordHasher(rounds=MIN_ROUNDS)

    def test_hash_password_returns_string(self):
        """Should return a string."""
        hashed = self.hasher.hash_password("secret")
        assert isinstance(hashed, str)

    def test_hash_password_has_bcrypt_prefix(self):
        """Result should look like a bcrypt hash."""
        hashed = self.hasher.hash_password("secret")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_hash_password_same_input_different_salts(self):
        """Two hashes of the same password should differ (random salt)."""
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

    def test_hash_password_too_long_raises(self):
        """Password > MAX_PASSWORD_BYTES bytes should raise ValueError."""
        long_password = "a" * (MAX_PASSWORD_BYTES + 1)  # ASCII 1 byte each
        with pytest.raises(ValueError):
            self.hasher.hash_password(long_password)

    def test_hash_password_max_length_accepted(self):
        """Password exactly MAX_PASSWORD_BYTES bytes should be accepted."""
        password = "a" * MAX_PASSWORD_BYTES
        hashed = self.hasher.hash_password(password)
        assert isinstance(hashed, str)

    def test_hash_password_unicode(self):
        """Unicode password should be hashed."""
        password = "pässwörd✓"
        hashed = self.hasher.hash_password(password)
        assert isinstance(hashed, str)


class TestBCryptPasswordHasherVerifyPassword:
    """Tests for verify_password."""

    def setup_method(self):
        self.hasher = BCryptPasswordHasher(rounds=MIN_ROUNDS)

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

    def test_verify_password_too_long_returns_false(self):
        """Verify with too-long password should catch ValueError and return False."""
        long_password = "a" * (MAX_PASSWORD_BYTES + 1)
        hashed = self.hasher.hash_password("secret")
        assert self.hasher.verify_password(long_password, hashed) is False

    def test_verify_roundtrip_unicode(self):
        """Hash and verify should work with unicode."""
        password = "pässwörd✓"
        hashed = self.hasher.hash_password(password)
        assert self.hasher.verify_password(password, hashed) is True
