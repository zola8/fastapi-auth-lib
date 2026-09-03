from abc import ABC
from abc import abstractmethod
from uuid import UUID

from src.fastapi_auth_lib.models.user import UserProfile


class AsyncUserProfileRepository(ABC):
    """
    Async repository contract for user profiles.

    Repository semantics:

    - Read methods return None when the entity does not exist.
    - Create methods raise DuplicateEntityException on uniqueness conflicts.
    - Update methods return None when the entity does not exist.
    - Update methods raise DuplicateEntityException on uniqueness conflicts.
    - Delete methods are idempotent and do not raise if the entity does not exist.

    SQL mapping:

    - SELECT returning zero rows -> None
    - INSERT unique constraint violation -> DuplicateEntityException
    - UPDATE affecting zero rows -> None
    - DELETE affecting zero rows -> no-op
    """

    @abstractmethod
    async def create_user(self, user: UserProfile) -> UserProfile:
        """
        Create a new user profile.

        Implementations are responsible for assigning `user_id` if it is missing.

        Raises:
            DuplicateEntityException: If a user with this email already exists.
        """
        raise NotImplementedError

    @abstractmethod
    async def find_user_by_id(self, user_id: UUID) -> UserProfile | None:
        """
        Find a user by id.

        Returns:
            The matching UserProfile, or None if no user exists with this id.
        """
        raise NotImplementedError

    @abstractmethod
    async def find_user_by_email(self, email: str) -> UserProfile | None:
        """
        Find a user by normalized email.

        Returns:
            The matching UserProfile, or None if no user exists with this email.
        """
        raise NotImplementedError

    @abstractmethod
    async def update_user(
        self,
        user_id: UUID,
        user: UserProfile,
    ) -> UserProfile | None:
        """
        Update an existing user profile.

        Returns:
            The updated UserProfile, or None if no user exists with this id.

        Raises:
            DuplicateEntityException: If the updated email conflicts with another user.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_user(
        self,
        user_id: UUID,
        hard_delete: bool = False,
    ) -> None:
        """
        Delete a user profile.

        If `hard_delete` is False, implementations should perform a soft delete,
        usually by setting:

            status = UserStatus.DELETED

        If `hard_delete` is True, implementations should permanently remove the
        user from storage.

        This method is idempotent.

        If the user does not exist, implementations should do nothing and should
        not raise an exception.
        """
        raise NotImplementedError

    @abstractmethod
    async def list_users(self) -> list[UserProfile]:
        """
        Return all user profiles.

        Returns:
            A list of users. Empty list if no users exist.
        """
        raise NotImplementedError
