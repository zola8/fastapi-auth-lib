from datetime import timedelta
from uuid import uuid4

import jwt
import pytest
from httpx2 import AsyncClient

from src.fastapi_auth_lib.core.utils import _now
from tests.conftest import TEST_ISSUER
from tests.conftest import TEST_SECRET

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
EMAIL = "alice@example.com"
PASSWORD = "StrongP@ss1"
AUTH_PREFIX = "/api/v1/auth"
USERS_PREFIX = "/api/v1/users"


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
    """
    Authenticate via the service directly and return an access token.
    Used because there's no /login/password endpoint yet.
    """
    auth_service = app.state.auth_service
    user = await auth_service.authenticate_with_password(email, password)
    pair = auth_service.create_token_pair(user)
    return pair.access_token


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# GET /users/me — authenticated
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_me_returns_current_user(client: AsyncClient, app):
    await _register_and_activate(client)
    token = await _get_access_token(app, EMAIL, PASSWORD)

    resp = await client.get(f"{USERS_PREFIX}/me", headers=_auth_header(token))

    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == EMAIL
    assert body["status"] == "active"
    assert "user_id" in body
    assert "roles" in body


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client: AsyncClient):
    resp = await client.get(f"{USERS_PREFIX}/me")

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_malformed_header_returns_401(client: AsyncClient):
    resp = await client.get(
        f"{USERS_PREFIX}/me",
        headers={"Authorization": "NotBearer abc123"},
    )

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_invalid_token_returns_401(client: AsyncClient):
    resp = await client.get(
        f"{USERS_PREFIX}/me",
        headers=_auth_header("invalid.jwt.token"),
    )

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_expired_token_returns_401(client: AsyncClient, app, token_service):
    """A token signed with a different secret is rejected."""
    await _register_and_activate(client)

    now = _now()
    fake_payload = {
        "sub": str(uuid4()),
        "type": "access",
        "iss": TEST_ISSUER,
        "iat": now,
        "exp": now + timedelta(hours=1),
    }

    fake_token = jwt.encode(fake_payload, TEST_SECRET + "wrong-secret", algorithm="HS256")

    resp = await client.get(
        f"{USERS_PREFIX}/me",
        headers=_auth_header(fake_token),
    )

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /users/get/{user_id}
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_user_by_id_returns_user(client: AsyncClient):
    await _register_and_activate(client)

    # Get the user_id from /me
    token = await _get_access_token(client._transport.app, EMAIL, PASSWORD)
    me_resp = await client.get(f"{USERS_PREFIX}/me", headers=_auth_header(token))
    user_id = me_resp.json()["user_id"]

    resp = await client.get(f"{USERS_PREFIX}/get/{user_id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == EMAIL
    assert body["user_id"] == user_id


@pytest.mark.asyncio
async def test_get_user_invalid_uuid_returns_422(client: AsyncClient):
    resp = await client.get(f"{USERS_PREFIX}/get/not-a-uuid")

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_user_nonexistent_uuid_returns_404(client: AsyncClient):
    from uuid import uuid4

    resp = await client.get(f"{USERS_PREFIX}/get/{uuid4()}")

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_me_route_not_captured_by_parameterized_route(client: AsyncClient, app):
    await _register_and_activate(client)
    token = await _get_access_token(app, EMAIL, PASSWORD)

    resp = await client.get(f"{USERS_PREFIX}/me", headers=_auth_header(token))

    # If this returns 422, the route ordering is broken
    assert resp.status_code == 200
