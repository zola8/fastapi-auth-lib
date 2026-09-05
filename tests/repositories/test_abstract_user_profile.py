import pytest

from src.fastapi_auth_lib.repositories.async_user_profile import AsyncUserProfileRepository


class TestAbstractRepository:
    """Tests for abstract base class."""

    def test_cannot_instantiate_abstract(self):
        """Abstract class should not be instantiable."""

        with pytest.raises(TypeError):
            AsyncUserProfileRepository()
