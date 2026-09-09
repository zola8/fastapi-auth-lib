import pytest

from src.fastapi_auth_lib.repositories.async_refresh_token import AsyncRefreshTokenRepository


class IncompleteRepository(AsyncRefreshTokenRepository):
    """Missing all abstract methods."""


class CompleteRepository(AsyncRefreshTokenRepository):
    """Implements all abstract methods."""

    async def create_refresh_token(self, token):
        return token

    async def find_refresh_token_by_hash(self, token_hash):
        return None

    async def delete_refresh_token(self, refresh_token_id):
        pass

    async def delete_all_for_user(self, user_id):
        pass


class TestAsyncRefreshTokenRepository:
    """Tests for the abstract base class."""

    def test_cannot_instantiate_abstract(self):
        """The abstract base class itself cannot be instantiated."""
        with pytest.raises(TypeError):
            AsyncRefreshTokenRepository()

    def test_cannot_instantiate_incomplete_subclass(self):
        """A subclass that doesn't implement all methods cannot be instantiated."""
        with pytest.raises(TypeError):
            IncompleteRepository()

    def test_can_instantiate_complete_subclass(self):
        """A subclass that implements all abstract methods can be instantiated."""
        repo = CompleteRepository()
        assert isinstance(repo, AsyncRefreshTokenRepository)

    def test_abstract_methods_set(self):
        """The abstract methods set should contain all four method names."""
        abstract_methods = AsyncRefreshTokenRepository.__abstractmethods__
        assert "create_refresh_token" in abstract_methods
        assert "find_refresh_token_by_hash" in abstract_methods
        assert "delete_refresh_token" in abstract_methods
        assert "delete_all_for_user" in abstract_methods
