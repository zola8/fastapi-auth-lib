import uuid

from src.fastapi_auth_lib.core.constants import AUTH_IDENTITY_ENTITY
from src.fastapi_auth_lib.core.exceptions import DuplicateEntityException
from src.fastapi_auth_lib.core.utils import _now
from src.fastapi_auth_lib.core.utils import normalize_email
from src.fastapi_auth_lib.models.auth_identity import AuthIdentity
from src.fastapi_auth_lib.models.base import AuthProvider
from src.fastapi_auth_lib.repositories.async_auth_identity import AsyncAuthIdentityRepository

SubjectKey = tuple[AuthProvider, str]


class InMemoryAsyncAuthIdentityRepository(AsyncAuthIdentityRepository):
    """
    In-memory implementation of AsyncAuthIdentityRepository.

    Each user has at most one auth identity.

    Storage mirrors a SQL table with UNIQUE indexes:
        _identities:      auth_identity_id -> AuthIdentity
        _subjects:        (provider, normalized provider_subject) -> auth_identity_id
        _user_identities: user_id -> auth_identity_id  (UNIQUE, 1:1)
    """

    def __init__(self) -> None:
        self._identities: dict[int, AuthIdentity] = {}
        self._subjects: dict[SubjectKey, int] = {}
        self._user_identities: dict[uuid.UUID, int] = {}
        self._next_id = 1

    @staticmethod
    def _normalize_subject(provider: AuthProvider, provider_subject: str) -> str:
        if provider == AuthProvider.PASSWORD:
            return normalize_email(provider_subject)
        return provider_subject.strip()

    async def create_auth_identity(self, auth_identity: AuthIdentity) -> AuthIdentity:
        subject = self._normalize_subject(
            auth_identity.provider, auth_identity.provider_subject
        )
        subject_key = (auth_identity.provider, subject)

        if subject_key in self._subjects:
            raise DuplicateEntityException(
                entity_type=AUTH_IDENTITY_ENTITY,
                description=(
                    f"An identity for provider '{auth_identity.provider}' "
                    f"with this subject already exists"
                ),
            )

        if auth_identity.user_id in self._user_identities:
            raise DuplicateEntityException(
                entity_type=AUTH_IDENTITY_ENTITY,
                description="This user already has an authentication identity",
            )

        identity_id = auth_identity.auth_identity_id
        if identity_id is None:
            identity_id = self._next_id
            self._next_id += 1
        elif identity_id in self._identities:
            raise DuplicateEntityException(
                entity_type=AUTH_IDENTITY_ENTITY,
                description=f"An identity with id '{identity_id}' already exists",
            )
        else:
            self._next_id = max(self._next_id, identity_id + 1)

        stored = auth_identity.model_copy(deep=True)
        stored.auth_identity_id = identity_id
        stored.provider_subject = subject
        stored.updated_at = None

        self._identities[identity_id] = stored
        self._subjects[subject_key] = identity_id
        self._user_identities[stored.user_id] = identity_id

        return stored.model_copy(deep=True)

    async def find_auth_identity_by_id(
        self,
        auth_identity_id: int,
    ) -> AuthIdentity | None:
        stored = self._identities.get(auth_identity_id)
        return stored.model_copy(deep=True) if stored is not None else None

    async def find_auth_identity_by_user_id(
        self,
        user_id: uuid.UUID,
    ) -> AuthIdentity | None:
        identity_id = self._user_identities.get(user_id)
        if identity_id is None:
            return None
        stored = self._identities.get(identity_id)
        return stored.model_copy(deep=True) if stored is not None else None

    async def find_auth_identity_by_provider_subject(
        self,
        provider: AuthProvider,
        provider_subject: str,
    ) -> AuthIdentity | None:
        subject = self._normalize_subject(provider, provider_subject)
        identity_id = self._subjects.get((provider, subject))
        if identity_id is None:
            return None
        stored = self._identities.get(identity_id)
        return stored.model_copy(deep=True) if stored is not None else None

    async def update_auth_identity(
        self,
        auth_identity_id: int,
        auth_identity: AuthIdentity,
    ) -> AuthIdentity | None:
        stored = self._identities.get(auth_identity_id)
        if stored is None:
            return None

        new_subject = self._normalize_subject(
            auth_identity.provider, auth_identity.provider_subject
        )
        new_key = (auth_identity.provider, new_subject)

        owner = self._subjects.get(new_key)
        if owner is not None and owner != auth_identity_id:
            raise DuplicateEntityException(
                entity_type=AUTH_IDENTITY_ENTITY,
                description=(
                    f"An identity for provider '{auth_identity.provider}' "
                    f"with this subject already exists"
                ),
            )

        if auth_identity.user_id != stored.user_id:
            if auth_identity.user_id in self._user_identities:
                raise DuplicateEntityException(
                    entity_type=AUTH_IDENTITY_ENTITY,
                    description="The target user already has an authentication identity",
                )

        old_key = (stored.provider, stored.provider_subject)

        updated = auth_identity.model_copy(deep=True)
        updated.auth_identity_id = auth_identity_id
        updated.provider_subject = new_subject
        updated.created_at = stored.created_at
        updated.updated_at = _now()

        self._identities[auth_identity_id] = updated
        if old_key != new_key:
            self._subjects.pop(old_key, None)
            self._subjects[new_key] = auth_identity_id

        if updated.user_id != stored.user_id:
            del self._user_identities[stored.user_id]
            self._user_identities[updated.user_id] = auth_identity_id

        return updated.model_copy(deep=True)

    async def delete_auth_identity(self, auth_identity_id: int) -> None:
        stored = self._identities.pop(auth_identity_id, None)
        if stored is None:
            return

        self._subjects.pop((stored.provider, stored.provider_subject), None)
        self._user_identities.pop(stored.user_id, None)
