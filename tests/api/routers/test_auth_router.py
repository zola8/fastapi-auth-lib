import pytest

AUTH = "/api/v1/auth"
EMAIL = "alice@example.com"
PASSWORD = "a" * 8
NEW_PASSWORD = "b" * 9


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _register(client, email=EMAIL, password=PASSWORD):
    return await client.post(
        f"{AUTH}/register/password",
        json={"email": email, "password": password},
    )


async def _register_and_activate(client, email=EMAIL, password=PASSWORD):
    resp = await _register(client, email, password)
    token = resp.json()["activation_token"]
    await client.get(f"{AUTH}/activate", params={"token": token})
    return email, password


async def _login(client, email=EMAIL, password=PASSWORD):
    resp = await client.post(
        f"{AUTH}/login/password",
        json={"email": email, "password": password},
    )
    return resp


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# POST /auth/register/password
# ---------------------------------------------------------------------------
class TestRegister:
    @pytest.mark.asyncio
    async def test_register_returns_201(self, client):
        resp = await _register(client)

        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == EMAIL
        assert "user_id" in body
        assert len(body["activation_token"]) > 0

    @pytest.mark.asyncio
    async def test_register_normalizes_email(self, client):
        resp = await _register(client, email="  ALICE@Example.COM  ")

        assert resp.status_code == 201
        assert resp.json()["email"] == "alice@example.com"

    @pytest.mark.asyncio
    async def test_register_duplicate_returns_409(self, client):
        await _register(client)
        resp = await _register(client)

        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_register_short_password_returns_422(self, client):
        resp = await _register(client, password="short")

        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /auth/activate
# ---------------------------------------------------------------------------
class TestActivate:
    @pytest.mark.asyncio
    async def test_activate_success(self, client):
        reg = await _register(client)
        token = reg.json()["activation_token"]

        resp = await client.get(f"{AUTH}/activate", params={"token": token})

        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

    @pytest.mark.asyncio
    async def test_activate_idempotent(self, client):
        reg = await _register(client)
        token = reg.json()["activation_token"]

        await client.get(f"{AUTH}/activate", params={"token": token})
        resp = await client.get(f"{AUTH}/activate", params={"token": token})

        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

    @pytest.mark.asyncio
    async def test_activate_invalid_token_returns_401(self, client):
        resp = await client.get(f"{AUTH}/activate", params={"token": "garbage"})

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_activate_missing_token_returns_422(self, client):
        resp = await client.get(f"{AUTH}/activate")

        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /auth/resend-activation
# ---------------------------------------------------------------------------
class TestResendActivation:
    @pytest.mark.asyncio
    async def test_resend_inactive_account(self, client):
        await _register(client)

        resp = await client.post(
            f"{AUTH}/resend-activation",
            json={"email": EMAIL},
        )

        assert resp.status_code == 200
        assert "message" in resp.json()

    @pytest.mark.asyncio
    async def test_resend_unknown_email_same_response(self, client):
        """Anti-enumeration: unknown email returns identical response."""
        resp = await client.post(
            f"{AUTH}/resend-activation",
            json={"email": "nobody@example.com"},
        )

        assert resp.status_code == 200
        assert "message" in resp.json()

    @pytest.mark.asyncio
    async def test_resend_active_account_same_response(self, client):
        await _register_and_activate(client)

        resp = await client.post(
            f"{AUTH}/resend-activation",
            json={"email": EMAIL},
        )

        assert resp.status_code == 200
        assert "message" in resp.json()


# ---------------------------------------------------------------------------
# POST /auth/login/password
# ---------------------------------------------------------------------------
class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, client):
        await _register_and_activate(client)

        resp = await _login(client)

        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["access_token"].count(".") == 2
        assert body["refresh_token"].count(".") == 2

    @pytest.mark.asyncio
    async def test_login_wrong_password_returns_401(self, client):
        await _register_and_activate(client)

        resp = await _login(client, password="WrongP@ss!")

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_unknown_email_returns_401(self, client):
        resp = await _login(client, email="ghost@example.com")

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_inactive_user_returns_401(self, client):
        await _register(client)  # registered but NOT activated

        resp = await _login(client)

        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------
class TestRefresh:
    @pytest.mark.asyncio
    async def test_refresh_returns_new_pair(self, client):
        await _register_and_activate(client)
        login = await _login(client)
        refresh_token = login.json()["refresh_token"]

        resp = await client.post(
            f"{AUTH}/refresh",
            json={"refresh_token": refresh_token},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        # Rotation: new refresh token differs from the old one
        assert body["refresh_token"] != refresh_token

    @pytest.mark.asyncio
    async def test_refresh_old_token_after_rotation_fails(self, client):
        """After rotation, the old refresh token is revoked."""
        await _register_and_activate(client)
        login = await _login(client)
        old_refresh = login.json()["refresh_token"]

        # Rotate once
        await client.post(f"{AUTH}/refresh", json={"refresh_token": old_refresh})

        # Old token is now revoked
        resp = await client.post(
            f"{AUTH}/refresh",
            json={"refresh_token": old_refresh},
        )

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_invalid_token_returns_401(self, client):
        resp = await client.post(
            f"{AUTH}/refresh",
            json={"refresh_token": "not.a.valid.jwt"},
        )

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_with_access_token_returns_401(self, client):
        """An access token cannot be used as a refresh token."""
        await _register_and_activate(client)
        login = await _login(client)
        access_token = login.json()["access_token"]

        resp = await client.post(
            f"{AUTH}/refresh",
            json={"refresh_token": access_token},
        )

        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------
class TestLogout:
    @pytest.mark.asyncio
    async def test_logout_success(self, client):
        await _register_and_activate(client)
        login = await _login(client)
        body = login.json()

        resp = await client.post(
            f"{AUTH}/logout",
            json={"refresh_token": body["refresh_token"]},
            headers=_auth_header(body["access_token"]),
        )

        assert resp.status_code == 200
        assert "message" in resp.json()

    @pytest.mark.asyncio
    async def test_logout_without_bearer_returns_401(self, client):
        await _register_and_activate(client)
        login = await _login(client)

        resp = await client.post(
            f"{AUTH}/logout",
            json={"refresh_token": login.json()["refresh_token"]},
        )

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_revokes_refresh_token(self, client):
        """After logout, the refresh token can no longer be used."""
        await _register_and_activate(client)
        login = await _login(client)
        body = login.json()

        # Logout
        await client.post(
            f"{AUTH}/logout",
            json={"refresh_token": body["refresh_token"]},
            headers=_auth_header(body["access_token"]),
        )

        # Try to refresh with the revoked token
        resp = await client.post(
            f"{AUTH}/refresh",
            json={"refresh_token": body["refresh_token"]},
        )

        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /auth/logout-everywhere
# ---------------------------------------------------------------------------
class TestLogoutEverywhere:
    @pytest.mark.asyncio
    async def test_logout_everywhere_success(self, client):
        await _register_and_activate(client)
        login = await _login(client)
        access_token = login.json()["access_token"]

        resp = await client.post(
            f"{AUTH}/logout-everywhere",
            headers=_auth_header(access_token),
        )

        assert resp.status_code == 200
        assert "message" in resp.json()

    @pytest.mark.asyncio
    async def test_logout_everywhere_revokes_all_sessions(self, client):
        """Multiple sessions are all revoked after logout-everywhere."""
        await _register_and_activate(client)

        # Log in from two "devices"
        login1 = await _login(client)
        login2 = await _login(client)

        # Logout everywhere using device 1's access token
        await client.post(
            f"{AUTH}/logout-everywhere",
            headers=_auth_header(login1.json()["access_token"]),
        )

        # Both refresh tokens should now be revoked
        resp1 = await client.post(
            f"{AUTH}/refresh",
            json={"refresh_token": login1.json()["refresh_token"]},
        )
        resp2 = await client.post(
            f"{AUTH}/refresh",
            json={"refresh_token": login2.json()["refresh_token"]},
        )

        assert resp1.status_code == 401
        assert resp2.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_everywhere_without_bearer_returns_401(self, client):
        resp = await client.post(f"{AUTH}/logout-everywhere")

        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /auth/forgot-password
# ---------------------------------------------------------------------------
class TestForgotPassword:
    @pytest.mark.asyncio
    async def test_forgot_password_active_account(self, client):
        await _register_and_activate(client)

        resp = await client.post(
            f"{AUTH}/forgot-password",
            json={"email": EMAIL},
        )

        assert resp.status_code == 200
        assert "message" in resp.json()

    @pytest.mark.asyncio
    async def test_forgot_password_unknown_email_same_response(self, client):
        resp = await client.post(
            f"{AUTH}/forgot-password",
            json={"email": "ghost@example.com"},
        )

        assert resp.status_code == 200
        assert "message" in resp.json()

    @pytest.mark.asyncio
    async def test_forgot_password_inactive_account_same_response(self, client):
        await _register(client)  # not activated

        resp = await client.post(
            f"{AUTH}/forgot-password",
            json={"email": EMAIL},
        )

        assert resp.status_code == 200
        assert "message" in resp.json()


# ---------------------------------------------------------------------------
# POST /auth/reset-password
# ---------------------------------------------------------------------------
class TestResetPassword:
    @pytest.mark.asyncio
    async def test_reset_password_full_flow(self, client, app):
        """Register → activate → request reset → extract token → reset → login with new password."""
        await _register_and_activate(client)

        # Get reset token via service (since email is dummy/disabled)
        auth_service = app.state.auth_service
        result = await auth_service.request_password_reset(EMAIL)
        assert result is not None
        _, reset_token = result

        # Reset the password
        resp = await client.post(
            f"{AUTH}/reset-password",
            json={"token": reset_token, "new_password": NEW_PASSWORD},
        )

        assert resp.status_code == 200
        assert resp.json()["message"] == "Password updated successfully."

        # Login with NEW password works
        resp = await _login(client, password=NEW_PASSWORD)
        assert resp.status_code == 200

        # Login with OLD password fails
        resp = await _login(client, password=PASSWORD)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token_returns_401(self, client):
        resp = await client.post(
            f"{AUTH}/reset-password",
            json={"token": "invalid.token.here", "new_password": NEW_PASSWORD},
        )

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_reset_password_short_password_returns_422(self, client):
        resp = await client.post(
            f"{AUTH}/reset-password",
            json={"token": "some-token", "new_password": "short"},
        )

        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Full lifecycle: register → activate → login → refresh → logout
# ---------------------------------------------------------------------------
class TestFullLifecycle:
    @pytest.mark.asyncio
    async def test_complete_auth_flow(self, client):
        # 1. Register
        reg = await _register(client)
        assert reg.status_code == 201
        activation_token = reg.json()["activation_token"]

        # 2. Activate
        act = await client.get(f"{AUTH}/activate", params={"token": activation_token})
        assert act.status_code == 200

        # 3. Login
        login = await _login(client)
        assert login.status_code == 200
        tokens = login.json()

        # 4. Refresh (rotation)
        refresh_resp = await client.post(
            f"{AUTH}/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert refresh_resp.status_code == 200
        new_tokens = refresh_resp.json()
        assert new_tokens["refresh_token"] != tokens["refresh_token"]

        # 5. Old refresh token is dead
        old_refresh = await client.post(
            f"{AUTH}/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert old_refresh.status_code == 401

        # 6. Logout with new tokens
        logout = await client.post(
            f"{AUTH}/logout",
            json={"refresh_token": new_tokens["refresh_token"]},
            headers=_auth_header(new_tokens["access_token"]),
        )
        assert logout.status_code == 200

        # 7. Refresh after logout fails
        final = await client.post(
            f"{AUTH}/refresh",
            json={"refresh_token": new_tokens["refresh_token"]},
        )
        assert final.status_code == 401
