import asyncio
import uuid
from typing import Dict
from typing import Tuple

from fastapi_auth_lib.core.exceptions import DuplicateEntityException
from fastapi_auth_lib.core.exceptions import EntityNotFoundException
from fastapi_auth_lib.core.utils import _now
from fastapi_auth_lib.models.auth_identity import AuthIdentity
from fastapi_auth_lib.models.base import AUTH_IDENTITY_ENTITY
from fastapi_auth_lib.models.base import AuthProvider
from fastapi_auth_lib.repositories.auth_identity_repo_interface import AuthIdentityRepository


class InMemoryAuthIdentityRepository(AuthIdentityRepository):
    """Own implementation of in-memory AuthIdentityRepository (one identity per user)."""

    def __init__(self) -> None:
        self._auth_identities: Dict[int, AuthIdentity] = {}
        self._next_auth_identity_id: int = 1

        # (provider, provider_subject)
        self._auth_identity_id_by_provider_subject: Dict[
            Tuple[AuthProvider, str], int
        ] = {}

        # unique by user_id, auth_identity_id (one-to-one)
        self._auth_identity_id_by_user_id: Dict[uuid.UUID, int] = {}
        self._lock = asyncio.Lock()

    async def create_auth_identity(self, auth_identity: AuthIdentity) -> AuthIdentity:
        async with self._lock:
            self._assert_provider_subject_available(
                provider=auth_identity.provider,
                provider_subject=auth_identity.provider_subject,
            )
            self._assert_user_id_available(auth_identity.user_id)

            auth_identity_id = self._next_auth_identity_id
            self._next_auth_identity_id += 1

            new_identity = auth_identity.model_copy(deep=True)
            new_identity.auth_identity_id = auth_identity_id
            new_identity.created_at = _now()
            new_identity.updated_at = None

            self._auth_identities[auth_identity_id] = new_identity
            self._index_auth_identity(new_identity)

            return new_identity.model_copy(deep=True)

    async def get_auth_identity(self, auth_identity_id: int) -> AuthIdentity:
        async with self._lock:
            identity = self._get_stored_or_raise(auth_identity_id)
            return identity.model_copy(deep=True)

    async def get_auth_identity_by_user_id(self, user_id: uuid.UUID) -> AuthIdentity:
        async with self._lock:
            auth_identity_id = self._auth_identity_id_by_user_id.get(user_id)

            if auth_identity_id is None:
                raise EntityNotFoundException(
                    field="user_id",
                    value=str(user_id),
                    entity_type=AUTH_IDENTITY_ENTITY,
                )

            return self._auth_identities[auth_identity_id].model_copy(deep=True)

    async def get_auth_identity_by_provider_subject(
        self,
        provider: AuthProvider,
        provider_subject: str,
    ) -> AuthIdentity:
        async with self._lock:
            auth_identity_id = self._auth_identity_id_by_provider_subject.get(
                (provider, provider_subject)
            )

            if auth_identity_id is None:
                raise EntityNotFoundException(
                    field="provider_subject",
                    value=provider_subject,
                    entity_type=AUTH_IDENTITY_ENTITY,
                )

            return self._auth_identities[auth_identity_id].model_copy(deep=True)

    async def update_auth_identity(
        self,
        auth_identity_id: int,
        auth_identity: AuthIdentity,
    ) -> AuthIdentity:
        async with self._lock:
            existing = self._get_stored_or_raise(auth_identity_id)
            self._assert_provider_subject_available_for_update(
                provider=existing.provider,
                provider_subject=auth_identity.provider_subject,
                auth_identity_id=auth_identity_id,
            )

            updated = auth_identity.model_copy(deep=True)
            # Mutable fields - provider_subject, password_hash

            # Immutable fields
            updated.auth_identity_id = auth_identity_id
            updated.user_id = existing.user_id
            updated.provider = existing.provider
            updated.created_at = existing.created_at
            updated.updated_at = _now()

            self._deindex_auth_identity(existing)
            self._auth_identities[auth_identity_id] = updated
            self._index_auth_identity(updated)

            return updated.model_copy(deep=True)

    async def delete_auth_identity(self, auth_identity_id: int) -> None:
        async with self._lock:
            existing = self._get_stored_or_raise(auth_identity_id)
            self._deindex_auth_identity(existing)
            del self._auth_identities[auth_identity_id]

    def _get_stored_or_raise(self, auth_identity_id: int) -> AuthIdentity:
        self._validate_auth_identity_id(auth_identity_id)

        identity = self._auth_identities.get(auth_identity_id)

        if identity is None:
            raise EntityNotFoundException(
                field="auth_identity_id",
                value=auth_identity_id,
                entity_type=AUTH_IDENTITY_ENTITY,
            )

        return identity

    def _validate_auth_identity_id(self, auth_identity_id: int) -> None:
        if isinstance(auth_identity_id, bool) or not isinstance(auth_identity_id, int) or auth_identity_id <= 0:
            raise EntityNotFoundException(
                field="auth_identity_id",
                value=auth_identity_id,
                entity_type=AUTH_IDENTITY_ENTITY,
            )

    def _assert_provider_subject_available(
        self, provider: AuthProvider, provider_subject: str
    ) -> None:
        if (provider, provider_subject) in self._auth_identity_id_by_provider_subject:
            raise DuplicateEntityException(
                field="provider_subject",
                value=provider_subject,
                entity_type=AUTH_IDENTITY_ENTITY,
            )

    def _assert_provider_subject_available_for_update(
        self, provider: AuthProvider, provider_subject: str, auth_identity_id: int
    ) -> None:
        existing_id = self._auth_identity_id_by_provider_subject.get(
            (provider, provider_subject)
        )

        if existing_id and existing_id != auth_identity_id:
            raise DuplicateEntityException(
                field="provider_subject",
                value=provider_subject,
                entity_type=AUTH_IDENTITY_ENTITY,
            )

    def _assert_user_id_available(self, user_id: uuid.UUID) -> None:
        if user_id in self._auth_identity_id_by_user_id:
            raise DuplicateEntityException(
                field="user_id",
                value=str(user_id),
                entity_type=AUTH_IDENTITY_ENTITY,
            )

    def _index_auth_identity(self, identity: AuthIdentity) -> None:
        if identity.auth_identity_id is None:
            return

        provider_subject = identity.provider_subject

        self._auth_identity_id_by_provider_subject[
            (identity.provider, provider_subject)
        ] = identity.auth_identity_id

        self._auth_identity_id_by_user_id[identity.user_id] = (
            identity.auth_identity_id
        )

    def _deindex_auth_identity(self, identity: AuthIdentity) -> None:
        if identity.auth_identity_id is None:
            return

        provider_subject = identity.provider_subject

        key = (identity.provider, provider_subject)
        if self._auth_identity_id_by_provider_subject.get(key) == identity.auth_identity_id:
            del self._auth_identity_id_by_provider_subject[key]

        if self._auth_identity_id_by_user_id.get(identity.user_id) == identity.auth_identity_id:
            del self._auth_identity_id_by_user_id[identity.user_id]
