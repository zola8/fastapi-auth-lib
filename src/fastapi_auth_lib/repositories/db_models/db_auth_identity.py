from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UUID
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from fastapi_auth_lib.models.base import AuthProvider
from fastapi_auth_lib.repositories.db_models.db_base import Base
from fastapi_auth_lib.repositories.db_models.db_user_profile import DBUserProfile


class DBAuthIdentity(Base):
    __tablename__ = "auth_identity"
    __table_args__ = (
        UniqueConstraint(
            "provider", "provider_subject", name="uq_auth_identity_provider_subject"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profile.user_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    provider: Mapped[AuthProvider] = mapped_column(
        Enum(AuthProvider, name="provider", create_constraint=True), nullable=False
    )

    provider_subject: Mapped[str] = mapped_column(String, nullable=False)

    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user_profile: Mapped["DBUserProfile"] = relationship(
        "DBUserProfile", back_populates="auth_identity"
    )

    def __repr__(self):
        return f"<DBAuthIdentity(id={self.id}, provider={self.provider})>"
