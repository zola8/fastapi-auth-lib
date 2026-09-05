import logging

import pytest

from src.fastapi_auth_lib.services.password_hasher.plain_text_hasher import PlaintextHasher


class TestPlaintextHasher:
    """Tests for the PlaintextHasher class."""

    def setup_method(self):
        self.hasher = PlaintextHasher()

    def test_constructor_logs_warning(self, caplog):
        """Should emit a warning log when instantiated."""
        with caplog.at_level(logging.WARNING):
            PlaintextHasher()
        assert "PlaintextHasher" in caplog.text
        assert "never use this in production" in caplog.text.lower()

    def test_hash_password_returns_same_string(self):
        """hash_password should return the input password unchanged."""
        assert self.hasher.hash_password("secret") == "secret"
        assert self.hasher.hash_password("p@ssw0rd") == "p@ssw0rd"
        assert self.hasher.hash_password("123456") == "123456"

    def test_hash_password_raises_on_none(self):
        """None password should raise ValueError."""
        with pytest.raises(ValueError):
            self.hasher.hash_password(None)

    def test_hash_password_raises_on_empty_string(self):
        """Empty string password should raise ValueError."""
        with pytest.raises(ValueError):
            self.hasher.hash_password("")

    def test_hash_password_allows_whitespace(self):
        """Whitespace-only passwords are not empty and should be stored as-is."""
        password = "   "
        assert self.hasher.hash_password(password) == password

    def test_verify_password_correct(self):
        """verify_password should return True when passwords match."""
        assert self.hasher.verify_password("secret", "secret") is True

    def test_verify_password_incorrect(self):
        """verify_password should return False when passwords differ."""
        assert self.hasher.verify_password("secret", "wrong") is False

    def test_verify_password_with_none_password(self):
        """verify_password should return False when password is None."""
        assert self.hasher.verify_password(None, "secret") is False

    def test_verify_password_with_none_hashed(self):
        """verify_password should return False when hashed_password is None."""
        assert self.hasher.verify_password("secret", None) is False

    def test_verify_password_with_both_none(self):
        """verify_password should return False when both are None."""
        assert self.hasher.verify_password(None, None) is False

    def test_verify_password_empty_strings(self):
        """verify_password should return False when either is empty."""
        assert self.hasher.verify_password("", "") is False
        assert self.hasher.verify_password("secret", "") is False
        assert self.hasher.verify_password("", "secret") is False

    def test_verify_password_whitespace_match(self):
        """Whitespace-only passwords should match if equal."""
        assert self.hasher.verify_password("   ", "   ") is True

    def test_verify_password_whitespace_mismatch(self):
        """Different whitespace strings should not match."""
        assert self.hasher.verify_password("   ", "  ") is False
