from enum import StrEnum


class UserStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


class AuthProvider(StrEnum):
    PASSWORD = "password"


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


USER_ENTITY = "User"
AUTH_IDENTITY_ENTITY = "AuthIdentity"
