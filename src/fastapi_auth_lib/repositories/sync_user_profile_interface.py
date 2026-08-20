import uuid
from abc import ABC, abstractmethod

from fastapi_auth_lib.models.user import UserProfile


class IUserProfileRepository(ABC):
    """Abstract synchronous CRUD repository for user profiles."""

    @abstractmethod
    def create_user(self, user: UserProfile) -> UserProfile:
        """
        Create a new user.
        The implementation generates and assigns `user_id`.
        Raises:
            DuplicateEntityException: If a user with the same email already exists.
            DuplicateEntityException: If username is unique and already exists.
        """
        raise NotImplementedError

    @abstractmethod
    def get_user_by_id(self, user_id: uuid.UUID) -> UserProfile:
        """
        Get a user by user_id.
        Raises:
            EntityNotFoundException: If user does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def get_user_by_email(self, email: str) -> UserProfile:
        """
        Get a user by normalized email.
        Raises:
            EntityNotFoundException: If user does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def update_user(self, user_id: uuid.UUID, user: UserProfile) -> UserProfile:
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
    def delete_user(self, user_id: uuid.UUID, hard_delete: bool = False) -> None:
        """
        Delete a user.
        If `hard_delete` is False, perform a soft delete by setting status = DELETED.
        If `hard_delete` is True, permanently remove the user from storage.
        Raises:
            EntityNotFoundException: If user does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def get_all_users(self) -> list[UserProfile]:
        """
        Get all users.
        Returns an empty list if no users exist.
        """
        raise NotImplementedError
