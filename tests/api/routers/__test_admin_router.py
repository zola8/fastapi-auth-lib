import pytest
from httpx2 import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
EMAIL = "alice@example.com"
PASSWORD = "StrongP@ss1"
AUTH_PREFIX = "/api/v1/auth"
ADMIN_PREFIX = "/api/v1/admin"


async def _register_and_activate(client: AsyncClient, email: str = EMAIL, password: str = PASSWORD):
    """Register, activate, and return (email, password)."""
    resp = await client.post(
        f"{AUTH_PREFIX}/register/password",
        json={"email": email, "password": password},
    )
    token = resp.json()["activation_token"]
    await client.get(f"{AUTH_PREFIX}/activate", params={"token": token})
    return email, password


async def _get_access_token(app, email: str, password: str) -> str:
    auth_service = app.state.auth_service
    user = await auth_service.authenticate_with_password(email, password)
    pair = auth_service.create_token_pair(user)
    return pair.access_token


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _make_admin(app, email: str) -> None:
    """Promote a user to admin via the in-memory user repo."""
    user_service = app.state.user_service
    user = await user_service.find_user_by_email(email)
    from src.fastapi_auth_lib.models.base import UserRole
    user.roles = [UserRole.ADMIN]
    await user_service.update_user(user.user_id, user)


# ---------------------------------------------------------------------------
# GET /admin/users — requires admin role
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_admin_list_users_as_admin_returns_200(client: AsyncClient, app):
    await _register_and_activate(client)
    await _make_admin(app, EMAIL)
    token = await _get_access_token(app, EMAIL, PASSWORD)

    resp = await client.get(f"{ADMIN_PREFIX}/users", headers=_auth_header(token))

    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert body[0]["email"] == EMAIL


@pytest.mark.asyncio
async def test_admin_list_users_as_regular_user_returns_403(client: AsyncClient, app):
    """A user with only the 'user' role must be rejected."""
    await _register_and_activate(client)
    # Do NOT promote to admin — default role is USER
    token = await _get_access_token(app, EMAIL, PASSWORD)

    resp = await client.get(f"{ADMIN_PREFIX}/users", headers=_auth_header(token))

    assert resp.status_code == 403
    assert "error_msg" in resp.json()


@pytest.mark.asyncio
async def test_admin_list_users_without_token_returns_401(client: AsyncClient):
    resp = await client.get(f"{ADMIN_PREFIX}/users")

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_list_users_with_invalid_token_returns_401(client: AsyncClient):
    resp = await client.get(
        f"{ADMIN_PREFIX}/users",
        headers=_auth_header("invalid.jwt.token"),
    )

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_list_users_returns_multiple_users(client: AsyncClient, app):
    """Admin can see all registered users."""
    await _register_and_activate(client, "admin@example.com", PASSWORD)
    await _make_admin(app, "admin@example.com")
    await _register_and_activate(client, "regular@example.com", PASSWORD)

    token = await _get_access_token(app, "admin@example.com", PASSWORD)
    resp = await client.get(f"{ADMIN_PREFIX}/users", headers=_auth_header(token))

    assert resp.status_code == 200
    emails = {u["email"] for u in resp.json()}
    assert "admin@example.com" in emails
    assert "regular@example.com" in emails


@pytest.mark.asyncio
async def test_admin_list_users_after_role_revoked_returns_403(client: AsyncClient, app):
    """If admin role is removed, subsequent requests are denied immediately."""
    from src.fastapi_auth_lib.models.base import UserRole

    await _register_and_activate(client)
    await _make_admin(app, EMAIL)
    token = await _get_access_token(app, EMAIL, PASSWORD)

    # Verify access works first
    resp = await client.get(f"{ADMIN_PREFIX}/users", headers=_auth_header(token))
    assert resp.status_code == 200

    # Revoke admin role
    user_service = app.state.user_service
    user = await user_service.find_user_by_email(EMAIL)
    user.roles = [UserRole.USER]
    await user_service.update_user(user.user_id, user)

    # Same token, but roles are re-checked from DB on every request
    resp = await client.get(f"{ADMIN_PREFIX}/users", headers=_auth_header(token))
    assert resp.status_code == 403
