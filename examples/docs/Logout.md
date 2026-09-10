# Logout Process

#### 1. Logout Request

The client sends the refresh token to POST /auth/logout along with a valid Bearer access token in the header.

#### 2. Access Token Verification

The backend verifies the Bearer access token's signature, expiry, and type to authenticate the requesting user.

#### 3. Refresh Token Revocation

The backend hashes the provided refresh token and deletes the matching row from the database, instantly invalidating
that specific session.

#### 4. Confirmation

The backend returns a success response; subsequent attempts to use the revoked refresh token at /auth/refresh will be
rejected.

#### 5. Logout Everywhere (Optional)

If the client calls POST /auth/logout-everywhere, the backend deletes all stored refresh token hashes for the
authenticated user, revoking every active session across all devices.

```mermaid
sequenceDiagram
    actor Client
    participant Router as API Router
    participant Auth as AsyncAuthService
    participant JWT as JwtTokenService
    participant DB as RefreshTokenRepo
    participant UserDB as User/Identity Repo
%% LOGOUT FLOW
    rect rgb(255, 240, 240)
        Note over Client, DB: Logout Process
        Client ->> Router: POST /auth/logout<br/>Header: Bearer <access><br/>Body: {refresh_token}
        Router ->> Auth: get_current_user(access_token)
        Auth ->> JWT: verify_access_token(access)
        JWT -->> Auth: return user_id
        Auth ->> UserDB: get_user(user_id) + check ACTIVE
        UserDB -->> Auth: return current_user
        Router ->> Auth: logout(refresh_token)
        Auth ->> Auth: hash = SHA256(refresh_token)
        Auth ->> DB: find_refresh_token_by_hash(hash)
        DB -->> Auth: return stored_token
        Auth ->> DB: delete_refresh_token(token_id)
        DB -->> Auth: deleted
        Router -->> Client: 200 OK "Session revoked"
    end

%% LOGOUT EVERYWHERE
    rect rgb(255, 245, 230)
        Note over Client, DB: Logout Everywhere
        Client ->> Router: POST /auth/logout-everywhere<br/>Header: Bearer <access>
        Router ->> Auth: logout_all_sessions(current_user.user_id)
        Auth ->> DB: delete_all_for_user(user_id)
        DB -->> Auth: all sessions deleted
        Router -->> Client: 200 OK "All sessions revoked"
    end
```
