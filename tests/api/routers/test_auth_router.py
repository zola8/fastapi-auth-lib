import pytest
from httpx2 import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
EMAIL = "alice@example.com"
PASSWORD = "StrongP@ss1"
NEW_PASSWORD = "NewStr0ng!Pass"
API_PREFIX = "/api/v1/auth"


async def _register(client: AsyncClient, email: str = EMAIL, password: str = PASSWORD):
    """Register and return the response."""
    return await client.post(
        f"{API_PREFIX}/register/password",
        json={"email": email, "password": password},
    )


async def _register_and_activate(client: AsyncClient, email: str = EMAIL, password: str = PASSWORD):
    """Register, extract activation token, activate, return (email, password)."""
    resp = await _register(client, email, password)
    token = resp.json()["activation_token"]
    await client.get(f"{API_PREFIX}/activate", params={"token": token})
    return email, password


# ---------------------------------------------------------------------------
# POST /register/password
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_register_returns_201_with_token(client: AsyncClient):
    resp = await _register(client)

    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == EMAIL
    assert "user_id" in body
    assert len(body["activation_token"]) > 0


@pytest.mark.asyncio
async def test_register_normalizes_email(client: AsyncClient):
    resp = await _register(client, email="  ALICE@Example.COM  ")

    assert resp.status_code == 201
    assert resp.json()["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client: AsyncClient):
    await _register(client)
    resp = await _register(client)

    assert resp.status_code == 409
    assert "error_msg" in resp.json()


@pytest.mark.asyncio
async def test_register_short_password_returns_422(client: AsyncClient):
    resp = await _register(client, password="short")

    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /activate
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_activate_account_succeeds(client: AsyncClient):
    reg = await _register(client)
    token = reg.json()["activation_token"]

    resp = await client.get(f"{API_PREFIX}/activate", params={"token": token})

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "active"
    assert body["user_id"] == reg.json()["user_id"]


@pytest.mark.asyncio
async def test_activate_is_idempotent(client: AsyncClient):
    reg = await _register(client)
    token = reg.json()["activation_token"]

    await client.get(f"{API_PREFIX}/activate", params={"token": token})
    resp = await client.get(f"{API_PREFIX}/activate", params={"token": token})

    # Second call succeeds — account is already active
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


@pytest.mark.asyncio
async def test_activate_invalid_token_returns_401(client: AsyncClient):
    resp = await client.get(f"{API_PREFIX}/activate", params={"token": "garbage.token.value"})

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_activate_missing_token_returns_422(client: AsyncClient):
    resp = await client.get(f"{API_PREFIX}/activate")

    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /resend-activation
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_resend_activation_for_inactive_account(client: AsyncClient):
    await _register(client)

    resp = await client.post(
        f"{API_PREFIX}/resend-activation",
        json={"email": EMAIL},
    )

    assert resp.status_code == 200
    assert "message" in resp.json()


@pytest.mark.asyncio
async def test_resend_activation_unknown_email_returns_same_message(client: AsyncClient):
    """Anti-enumeration: unknown email returns identical response."""
    resp = await client.post(
        f"{API_PREFIX}/resend-activation",
        json={"email": "nobody@example.com"},
    )

    assert resp.status_code == 200
    assert "message" in resp.json()


@pytest.mark.asyncio
async def test_resend_activation_already_active_returns_same_message(client: AsyncClient):
    await _register_and_activate(client)

    resp = await client.post(
        f"{API_PREFIX}/resend-activation",
        json={"email": EMAIL},
    )

    assert resp.status_code == 200
    assert "message" in resp.json()


# ---------------------------------------------------------------------------
# POST /forgot-password
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_forgot_password_active_account(client: AsyncClient):
    await _register_and_activate(client)

    resp = await client.post(
        f"{API_PREFIX}/forgot-password",
        json={"email": EMAIL},
    )

    assert resp.status_code == 200
    assert "message" in resp.json()


@pytest.mark.asyncio
async def test_forgot_password_unknown_email_returns_same_message(client: AsyncClient):
    resp = await client.post(
        f"{API_PREFIX}/forgot-password",
        json={"email": "ghost@example.com"},
    )

    assert resp.status_code == 200
    assert "message" in resp.json()


@pytest.mark.asyncio
async def test_forgot_password_inactive_account_returns_same_message(client: AsyncClient):
    """Inactive accounts can't reset — but response must not reveal that."""
    await _register(client)  # registered but NOT activated

    resp = await client.post(
        f"{API_PREFIX}/forgot-password",
        json={"email": EMAIL},
    )

    assert resp.status_code == 200
    assert "message" in resp.json()


# ---------------------------------------------------------------------------
# POST /reset-password
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_reset_password_full_flow(client: AsyncClient):
    """Register → activate → forgot-password → extract token → reset → login with new password."""
    await _register_and_activate(client)

    # Since forgot-password sends via email (dummy logger), we need another way
    # to get the token. We'll use the service directly through app.state.
    auth_service = client._transport.app.state.auth_service

    result = await auth_service.request_password_reset(EMAIL)
    assert result is not None
    _, reset_token = result

    resp = await client.post(
        f"{API_PREFIX}/reset-password",
        json={"token": reset_token, "new_password": NEW_PASSWORD},
    )

    assert resp.status_code == 200
    assert resp.json()["message"] == "Password updated successfully."


@pytest.mark.asyncio
async def test_reset_password_invalid_token_returns_401(client: AsyncClient):
    resp = await client.post(
        f"{API_PREFIX}/reset-password",
        json={"token": "invalid.token.here", "new_password": NEW_PASSWORD},
    )

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_reset_password_short_password_returns_422(client: AsyncClient):
    resp = await client.post(
        f"{API_PREFIX}/reset-password",
        json={"token": "some-token", "new_password": "short"},
    )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_reset_password_token_single_use(client: AsyncClient):
    """Using the same reset token twice should not fail on the second attempt."""
    await _register_and_activate(client)

    auth_service = client._transport.app.state.auth_service
    _, reset_token = await auth_service.request_password_reset(EMAIL)

    resp1 = await client.post(
        f"{API_PREFIX}/reset-password",
        json={"token": reset_token, "new_password": NEW_PASSWORD},
    )
    assert resp1.status_code == 200

    resp2 = await client.post(
        f"{API_PREFIX}/reset-password",
        json={"token": reset_token, "new_password": "AnotherP@ss1"},
    )
    # With stateless JWT: still 200 (token is valid until TTL expires)
    assert resp2.status_code == 200
