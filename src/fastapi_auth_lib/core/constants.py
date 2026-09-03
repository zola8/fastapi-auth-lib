"""
Central constants for fastapi_auth_lib.
"""

# --- Entity names (used in repository) ---
USER_ENTITY = "User"
AUTH_IDENTITY_ENTITY = "AuthIdentity"

# --- Username ---
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 64
USERNAME_PATTERN = r"^[a-zA-Z0-9_-]+$"

# --- Email ---
EMAIL_MAX_LENGTH = 254

# --- Password ---
PASSWORD_MIN_LENGTH = 6
PASSWORD_MAX_LENGTH = 128

# --- AuthIdentity ---
PROVIDER_SUBJECT_MAX_LENGTH = 255
PASSWORD_HASH_MAX_LENGTH = 512
