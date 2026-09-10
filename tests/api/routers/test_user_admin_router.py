import uuid

import pytest

from src.fastapi_auth_lib.models.base import UserRole

USERS = "/api/v1/users"
ADMIN = "/api/v1/admin"
AUTH = "/api/v1/auth"
EMAIL = "alice@example.com"
PASSWORD = "p" * 8


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _register_and_activate(client, email=EMAIL, password=PASSWORD):
    reg = await client.post(
        f"{AUTH}/register/password",
        json={"email": email, "password": password},
    )
    token = reg.json()["activation_token"]
    await client.get(f"{AUTH}/activate", params={"token": token})
    return email, password


async def _get_tokens(client, email=EMAIL, password=PASSWORD) -> dict:
    resp = await client.post(
        f"{AUTH}/login/password",
        json={"email": email, "password": password},
    )
    return resp.json()


async def _make_admin(app, email: str) -> None:
    """Promote a user to admin via the in-memory user service."""
    user_service = app.state.user_service
    user = await user_service.find_user_by_email(email)
    user.roles = [UserRole.ADMIN]
    await user_service.update_user(user.user_id, user)


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# GET /users/me
# ---------------------------------------------------------------------------
class TestUsersMe:
    @pytest.mark.asyncio
    async def test_me_returns_current_user(self, client, app):
        await _register_and_activate(client)
        tokens = await _get_tokens(client)

        resp = await client.get(
            f"{USERS}/me",
            headers=_auth_header(tokens["access_token"]),
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == EMAIL
        assert body["status"] == "active"
        assert "user_id" in body
        assert "roles" in body

    @pytest.mark.asyncio
    async def test_me_without_token_returns_401(self, client):
        resp = await client.get(f"{USERS}/me")

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_malformed_header_returns_401(self, client):
        resp = await client.get(
            f"{USERS}/me",
            headers={"Authorization": "Basic " + ("a" * 30)},
        )

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_invalid_token_returns_401(self, client):
        resp = await client.get(
            f"{USERS}/me",
            headers=_auth_header("invalid.jwt.token"),
        )

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_wrong_secret_token_returns_401(self, client):
        """A token signed with a different secret is rejected."""
        import jwt as pyjwt
        from datetime import datetime, timedelta, timezone

        payload = {
            "sub": str(uuid.uuid4()),
            "type": "access",
            "iss": "test-issuer",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "jti": str(uuid.uuid4()),
        }
        fake_token = pyjwt.encode(payload, "wrong-secret" * 3, algorithm="HS256")

        resp = await client.get(
            f"{USERS}/me",
            headers=_auth_header(fake_token),
        )

        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /admin/users
# ---------------------------------------------------------------------------
class TestAdminListUsers:
    @pytest.mark.asyncio
    async def test_list_users_as_admin_returns_200(self, client, app):
        await _register_and_activate(client)
        await _make_admin(app, EMAIL)
        tokens = await _get_tokens(client)

        resp = await client.get(
            f"{ADMIN}/users",
            headers=_auth_header(tokens["access_token"]),
        )

        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) >= 1
        assert body[0]["email"] == EMAIL

    @pytest.mark.asyncio
    async def test_list_users_as_regular_user_returns_403(self, client):
        await _register_and_activate(client)
        tokens = await _get_tokens(client)

        resp = await client.get(
            f"{ADMIN}/users",
            headers=_auth_header(tokens["access_token"]),
        )

        assert resp.status_code == 403
        assert "error_msg" in resp.json()

    @pytest.mark.asyncio
    async def test_list_users_without_token_returns_401(self, client):
        resp = await client.get(f"{ADMIN}/users")

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_list_users_returns_multiple_users(self, client, app):
        await _register_and_activate(client, "admin@example.com", PASSWORD)
        await _make_admin(app, "admin@example.com")
        await _register_and_activate(client, "regular@example.com", PASSWORD)

        tokens = await _get_tokens(client, "admin@example.com", PASSWORD)

        resp = await client.get(
            f"{ADMIN}/users",
            headers=_auth_header(tokens["access_token"]),
        )

        assert resp.status_code == 200
        emails = {u["email"] for u in resp.json()}
        assert "admin@example.com" in emails
        assert "regular@example.com" in emails

    @pytest.mark.asyncio
    async def test_list_users_after_role_revoked_returns_403(self, client, app):
        """If admin role is removed, subsequent requests are denied immediately."""
        await _register_and_activate(client)
        await _make_admin(app, EMAIL)
        tokens = await _get_tokens(client)

        # Verify access works first
        resp = await client.get(
            f"{ADMIN}/users",
            headers=_auth_header(tokens["access_token"]),
        )
        assert resp.status_code == 200

        # Revoke admin role
        user_service = app.state.user_service
        user = await user_service.find_user_by_email(EMAIL)
        user.roles = [UserRole.USER]
        await user_service.update_user(user.user_id, user)

        # Same access token, but roles are re-checked from DB
        resp = await client.get(
            f"{ADMIN}/users",
            headers=_auth_header(tokens["access_token"]),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /admin/get/{user_id}
# ---------------------------------------------------------------------------
class TestAdminGetUser:
    @pytest.mark.asyncio
    async def test_get_user_by_id_as_admin(self, client, app):
        await _register_and_activate(client)
        await _make_admin(app, EMAIL)
        tokens = await _get_tokens(client)

        # Get user_id from /users/me
        me = await client.get(
            f"{USERS}/me",
            headers=_auth_header(tokens["access_token"]),
        )
        user_id = me.json()["user_id"]

        resp = await client.get(
            f"{ADMIN}/get/{user_id}",
            headers=_auth_header(tokens["access_token"]),
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["user_id"] == user_id
        assert body["email"] == EMAIL

    @pytest.mark.asyncio
    async def test_get_user_as_regular_user_returns_403(self, client):
        await _register_and_activate(client)
        tokens = await _get_tokens(client)

        # Get user_id from /users/me
        me = await client.get(
            f"{USERS}/me",
            headers=_auth_header(tokens["access_token"]),
        )
        user_id = me.json()["user_id"]

        resp = await client.get(
            f"{ADMIN}/get/{user_id}",
            headers=_auth_header(tokens["access_token"]),
        )

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_get_user_without_token_returns_401(self, client):
        resp = await client.get(f"{ADMIN}/get/{uuid.uuid4()}")

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_user_invalid_uuid_returns_422(self, client, app):
        await _register_and_activate(client)
        await _make_admin(app, EMAIL)
        tokens = await _get_tokens(client)

        resp = await client.get(
            f"{ADMIN}/get/not-a-uuid",
            headers=_auth_header(tokens["access_token"]),
        )

        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_get_user_nonexistent_uuid_returns_404(self, client, app):
        await _register_and_activate(client)
        await _make_admin(app, EMAIL)
        tokens = await _get_tokens(client)

        resp = await client.get(
            f"{ADMIN}/get/{uuid.uuid4()}",
            headers=_auth_header(tokens["access_token"]),
        )

        assert resp.status_code == 404
