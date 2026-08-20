import uuid
from typing import NoReturn

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fastapi_auth_lib.core.exceptions import DuplicateEntityException
from fastapi_auth_lib.core.exceptions import EntityNotFoundException
from fastapi_auth_lib.core.utils import _now
from fastapi_auth_lib.models.auth_identity import AuthIdentity
from fastapi_auth_lib.models.base import AUTH_IDENTITY_ENTITY
from fastapi_auth_lib.models.base import AuthProvider
from fastapi_auth_lib.repositories.db_models.db_auth_identity import DBAuthIdentity
from fastapi_auth_lib.repositories.sync_auth_identity_interface import IAuthIdentityRepository


class SQLAlchemyIdentityRepository(IAuthIdentityRepository):
    """Synchronous SQLAlchemy implementation of IAuthIdentityRepository."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_auth_identity(self, auth_identity: AuthIdentity) -> AuthIdentity:
        self._assert_provider_subject_available(
            provider=auth_identity.provider,
            provider_subject=auth_identity.provider_subject,
        )
        self._assert_user_id_available(auth_identity.user_id)

        db_identity = DBAuthIdentity(
            user_id=auth_identity.user_id,
            provider=auth_identity.provider,
            provider_subject=auth_identity.provider_subject,
            password_hash=auth_identity.password_hash,
            created_at=_now(),
            updated_at=None,
        )

        self.session.add(db_identity)

        try:
            self.session.flush()
        except IntegrityError as error:
            self.session.rollback()
            self._raise_create_integrity_error(error, auth_identity)

        return self._to_dto(db_identity)

    def get_auth_identity(self, auth_identity_id: int) -> AuthIdentity:
        db_identity = self._get_entity_or_raise(auth_identity_id)
        return self._to_dto(db_identity)

    def get_auth_identity_by_user_id(self, user_id: uuid.UUID) -> AuthIdentity:
        stmt = (
            select(DBAuthIdentity)
            .where(DBAuthIdentity.user_id == user_id)
            .limit(1)
        )

        result = self.session.execute(stmt)
        db_identity = result.scalar_one_or_none()

        if db_identity is None:
            raise EntityNotFoundException(
                field="user_id",
                value=str(user_id),
                entity_type=AUTH_IDENTITY_ENTITY,
            )

        return self._to_dto(db_identity)

    def get_auth_identity_by_provider_subject(
        self,
        provider: AuthProvider,
        provider_subject: str,
    ) -> AuthIdentity:
        stmt = (
            select(DBAuthIdentity)
            .where(
                DBAuthIdentity.provider == provider,
                DBAuthIdentity.provider_subject == provider_subject,
            )
            .limit(1)
        )

        result = self.session.execute(stmt)
        db_identity = result.scalar_one_or_none()

        if db_identity is None:
            raise EntityNotFoundException(
                field="provider_subject",
                value=provider_subject,
                entity_type=AUTH_IDENTITY_ENTITY,
            )

        return self._to_dto(db_identity)

    def update_auth_identity(
        self,
        auth_identity_id: int,
        auth_identity: AuthIdentity,
    ) -> AuthIdentity:
        db_identity = self._get_entity_or_raise(auth_identity_id)

        provider = db_identity.provider
        new_provider_subject = auth_identity.provider_subject

        self._assert_provider_subject_available_for_update(
            provider=provider,
            provider_subject=new_provider_subject,
            auth_identity_id=auth_identity_id,
        )

        # Mutable fields
        db_identity.provider_subject = new_provider_subject
        db_identity.password_hash = auth_identity.password_hash
        db_identity.updated_at = _now()

        try:
            self.session.flush()
        except IntegrityError as error:
            self.session.rollback()

            if self._provider_subject_exists(
                provider=provider,
                provider_subject=new_provider_subject,
                exclude_id=auth_identity_id,
            ):
                raise DuplicateEntityException(
                    field="provider_subject",
                    value=new_provider_subject,
                    entity_type=AUTH_IDENTITY_ENTITY,
                ) from error

            raise error

        return self._to_dto(db_identity)

    def delete_auth_identity(self, auth_identity_id: int) -> None:
        db_identity = self._get_entity_or_raise(auth_identity_id)

        self.session.delete(db_identity)
        self.session.flush()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_entity_or_raise(self, auth_identity_id: int) -> DBAuthIdentity:
        self._validate_auth_identity_id(auth_identity_id)

        db_identity = self.session.get(DBAuthIdentity, auth_identity_id)

        if db_identity is None:
            raise EntityNotFoundException(
                field="auth_identity_id",
                value=auth_identity_id,
                entity_type=AUTH_IDENTITY_ENTITY,
            )

        return db_identity

    @staticmethod
    def _validate_auth_identity_id(auth_identity_id: int) -> None:
        if (
            isinstance(auth_identity_id, bool)
            or not isinstance(auth_identity_id, int)
            or auth_identity_id <= 0
        ):
            raise EntityNotFoundException(
                field="auth_identity_id",
                value=auth_identity_id,
                entity_type=AUTH_IDENTITY_ENTITY,
            )

    def _assert_provider_subject_available(
        self,
        provider: AuthProvider,
        provider_subject: str,
    ) -> None:
        if self._provider_subject_exists(
            provider=provider,
            provider_subject=provider_subject,
        ):
            raise DuplicateEntityException(
                field="provider_subject",
                value=provider_subject,
                entity_type=AUTH_IDENTITY_ENTITY,
            )

    def _assert_provider_subject_available_for_update(
        self,
        provider: AuthProvider,
        provider_subject: str,
        auth_identity_id: int,
    ) -> None:
        if self._provider_subject_exists(
            provider=provider,
            provider_subject=provider_subject,
            exclude_id=auth_identity_id,
        ):
            raise DuplicateEntityException(
                field="provider_subject",
                value=provider_subject,
                entity_type=AUTH_IDENTITY_ENTITY,
            )

    def _assert_user_id_available(self, user_id: uuid.UUID) -> None:
        if self._user_id_exists(user_id):
            raise DuplicateEntityException(
                field="user_id",
                value=str(user_id),
                entity_type=AUTH_IDENTITY_ENTITY,
            )

    def _provider_subject_exists(
        self,
        provider: AuthProvider,
        provider_subject: str,
        *,
        exclude_id: int | None = None,
    ) -> bool:
        stmt = (
            select(DBAuthIdentity.id)
            .where(
                DBAuthIdentity.provider == provider,
                DBAuthIdentity.provider_subject == provider_subject,
            )
            .limit(1)
        )

        if exclude_id is not None:
            stmt = stmt.where(DBAuthIdentity.id != exclude_id)

        result = self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    def _user_id_exists(self, user_id: uuid.UUID) -> bool:
        stmt = (
            select(DBAuthIdentity.id)
            .where(DBAuthIdentity.user_id == user_id)
            .limit(1)
        )

        result = self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    def _raise_create_integrity_error(
        self,
        error: IntegrityError,
        auth_identity: AuthIdentity,
    ) -> NoReturn:
        if self._provider_subject_exists(
            provider=auth_identity.provider,
            provider_subject=auth_identity.provider_subject,
        ):
            raise DuplicateEntityException(
                field="provider_subject",
                value=auth_identity.provider_subject,
                entity_type=AUTH_IDENTITY_ENTITY,
            ) from error

        if self._user_id_exists(auth_identity.user_id):
            raise DuplicateEntityException(
                field="user_id",
                value=str(auth_identity.user_id),
                entity_type=AUTH_IDENTITY_ENTITY,
            ) from error

        raise error

    @staticmethod
    def _to_dto(db_identity: DBAuthIdentity) -> AuthIdentity:
        return AuthIdentity(
            auth_identity_id=db_identity.id,
            user_id=db_identity.user_id,
            provider=db_identity.provider,
            provider_subject=db_identity.provider_subject,
            password_hash=db_identity.password_hash,
            created_at=db_identity.created_at,
            updated_at=db_identity.updated_at,
        )
