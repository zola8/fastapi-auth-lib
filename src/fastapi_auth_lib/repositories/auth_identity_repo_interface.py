import uuid
from abc import ABC
from abc import abstractmethod

from fastapi_auth_lib.models.auth_identity import AuthIdentity
from fastapi_auth_lib.models.base import AuthProvider


class AuthIdentityRepository(ABC):
    """Abstract CRUD repository for authentication identities (one per user)."""

    @abstractmethod
    async def create_auth_identity(self, auth_identity: AuthIdentity) -> AuthIdentity:
        """
        Create a new auth identity.

        Raises:
            DuplicateEntityException: If an identity with the same
                (provider, provider_subject) already exists.
            DuplicateEntityException: If the user_id already has an auth identity.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_auth_identity(self, auth_identity_id: int) -> AuthIdentity:
        """
        Get an auth identity by its primary id.

        Raises:
            EntityNotFoundException: If the auth identity does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_auth_identity_by_user_id(self, user_id: uuid.UUID) -> AuthIdentity:
        """
        Get the auth identity for a user.

        Raises:
            EntityNotFoundException: If the user has no auth identity.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_auth_identity_by_provider_subject(
        self,
        provider: AuthProvider,
        provider_subject: str,
    ) -> AuthIdentity:
        """
        Get an auth identity by provider and provider_subject.

        This is the main lookup used during login.

        Raises:
            EntityNotFoundException: If the auth identity does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    async def update_auth_identity(
        self,
        auth_identity_id: int,
        auth_identity: AuthIdentity,
    ) -> AuthIdentity:
        """
        Update an existing auth identity.

        Raises:
            EntityNotFoundException: If the auth identity does not exist.
            DuplicateEntityException: If provider_subject conflicts with
                another identity for the same provider.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_auth_identity(self, auth_identity_id: int) -> None:
        """
        Delete an auth identity.

        Raises:
            EntityNotFoundException: If the auth identity does not exist.
        """
        raise NotImplementedError
