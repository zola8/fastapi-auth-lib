import uuid
from abc import ABC
from abc import abstractmethod

from fastapi_auth_lib.models.user import UserProfile


class UserRepository(ABC):
    """Abstract CRUD repository for user profiles."""

    @abstractmethod
    async def create_user(self, user: UserProfile) -> UserProfile:
        """
        Create a new user.

        The implementation must generate and assign `user_id` if it is not set.

        Raises:
            DuplicateEntityException: If a user with the same email already exists.
            DuplicateEntityException: If username is unique and already exists.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_user_by_id(self, user_id: uuid) -> UserProfile:
        """
        Get a user by user_id.

        Raises:
            EntityNotFoundException: If user does not exist.
                Example:
                    EntityNotFoundException(
                        field="user_id",
                        value=user_id,
                        entity_type="User",
                    )
        """
        raise NotImplementedError

    @abstractmethod
    async def get_user_by_email(self, email: str) -> UserProfile:
        """
        Get a user by normalized email.

        Raises:
            EntityNotFoundException: If user does not exist.
                Example:
                    EntityNotFoundException(
                        field="email",
                        value=email,
                        entity_type="User",
                    )
        """
        raise NotImplementedError

    @abstractmethod
    async def update_user(self, user_id: uuid, user: UserProfile) -> UserProfile:
        """
        Update an existing user.

        The implementation should use `user_id` as the authoritative identifier
        and should not trust `user.user_id` if it differs.

        Raises:
            EntityNotFoundException: If user does not exist.
            DuplicateEntityException: If email or username conflicts with another user.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_user(self, user_id: uuid, hard_delete: bool = False) -> None:
        """
        Delete a user.

        If `hard_delete` is False, perform a soft delete, usually by setting:
            status = UserStatus.DELETED

        If `hard_delete` is True, permanently remove the user from storage.

        Raises:
            EntityNotFoundException: If user does not exist.
        """
        raise NotImplementedError
