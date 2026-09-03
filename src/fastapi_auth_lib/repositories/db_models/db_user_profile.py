from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy import UUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.fastapi_auth_lib.models.base import UserStatus
from src.fastapi_auth_lib.repositories.db_models.db_base import Base


class DBUserProfile(Base):
    __tablename__ = "user_profile"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True
    )

    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)

    username: Mapped[str | None] = mapped_column(String, nullable=True)

    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status", create_constraint=True),
        default=UserStatus.INACTIVE,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Set explicitly by the repository on update; no DB-level trigger",
    )

    roles: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="Must contain only valid UserRole values",
    )

    auth_identity: Mapped["DBAuthIdentity"] = relationship(
        "DBAuthIdentity",
        back_populates="user_profile",
        cascade="all, delete-orphan",
        lazy="selectin",
        uselist=False,  # one-to-one enforcement
    )

    def __repr__(self):
        return f"<DBUserProfile(user_id={self.user_id}, email={self.email}>"
