from abc import ABC
from abc import abstractmethod
from uuid import UUID

from src.fastapi_auth_lib.models.auth_identity import AuthIdentity
from src.fastapi_auth_lib.models.base import AuthProvider


class AsyncAuthIdentityRepository(ABC):
    """
    Async repository contract for authentication identities.

    Repository semantics:

    - Read methods return None when the identity does not exist.
    - Create methods raise DuplicateEntityException on uniqueness conflicts.
    - Update methods return None when the identity does not exist.
    - Update methods raise DuplicateEntityException on uniqueness conflicts.
    - Delete methods are idempotent and do not raise if the identity does not exist.

    SQL mapping:

    - SELECT returning zero rows -> None
    - INSERT unique constraint violation -> DuplicateEntityException
    - UPDATE affecting zero rows -> None
    - DELETE affecting zero rows -> no-op
    """

    @abstractmethod
    async def create_auth_identity(
        self,
        auth_identity: AuthIdentity,
    ) -> AuthIdentity:
        """
        Create a new authentication identity.

        Implementations are responsible for assigning `auth_identity_id` if it
        is missing.

        Required uniqueness invariant:

            (provider, provider_subject) must be unique.

        Raises:
            DuplicateEntityException: If an identity with this provider and subject already exists.
            DuplicateEntityException: If this user already has an authentication identity.
        """
        raise NotImplementedError

    @abstractmethod
    async def find_auth_identity_by_id(
        self,
        auth_identity_id: int,
    ) -> AuthIdentity | None:
        """
        Find an auth identity by its primary id.

        Returns:
            The matching AuthIdentity, or None if no identity exists with this id.
        """
        raise NotImplementedError

    @abstractmethod
    async def find_auth_identity_by_user_id(
        self,
        user_id: UUID,
    ) -> AuthIdentity | None:
        """
        Find an auth identity by user id.

        Returns:
            The matching AuthIdentity, or None if the user has no auth identity.
        """
        raise NotImplementedError

    @abstractmethod
    async def find_auth_identity_by_provider_subject(
        self,
        provider: AuthProvider,
        provider_subject: str,
    ) -> AuthIdentity | None:
        """
        Find an auth identity by provider and provider subject.
        This is the main lookup used during login.

        For password login, `provider_subject` should be the normalized email.

        Returns:
            The matching AuthIdentity, or None if no matching identity exists.
        """
        raise NotImplementedError

    @abstractmethod
    async def update_auth_identity(
        self,
        auth_identity_id: int,
        auth_identity: AuthIdentity,
    ) -> AuthIdentity | None:
        """
        Update an existing auth identity.

        Returns:
            The updated AuthIdentity, or None if no identity exists with this id.

        Raises:
            DuplicateEntityException:
                If the updated `(provider, provider_subject)` conflicts with
                another identity.

            DuplicateEntityException:
                If the implementation enforces one identity per user and the
                updated `user_id` conflicts with another identity.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_auth_identity(
        self,
        auth_identity_id: int,
    ) -> None:
        """
        Delete an auth identity.

        This method is idempotent.

        If the identity does not exist, implementations should do nothing and
        should not raise an exception.
        """
        raise NotImplementedError
