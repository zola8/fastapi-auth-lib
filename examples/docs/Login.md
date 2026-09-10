# Login Process

#### 1. Credential Submission

The client sends the user's email and password to POST /auth/login/password.

#### 2. Identity Lookup

The backend finds the auth identity by provider (password) and subject (normalized email).

#### 3. Password Verification

The submitted password is hashed using the configured hasher (for example: Argon2) and compared against the stored hash.

#### 4. Status Check

The backend verifies the user's account status is ACTIVE; inactive or deleted accounts are rejected.

#### 5. Access Token Issuance

A stateless JWT access token is created containing the user ID, a short TTL (default 30 min), and a unique jti claim.

#### 6. Refresh Token Issuance

A stateless JWT refresh token is created with a longer TTL (default 7 days), and its SHA-256 hash is stored in the
database for server-side revocation.

#### 7. Token Delivery

Both tokens are returned to the client as a TokenPairResponse.

```mermaid
sequenceDiagram
    actor Client
    participant Router as API Router
    participant Auth as AsyncAuthService
    participant JWT as JwtTokenService
    participant DB as RefreshTokenRepo
    participant UserDB as User/Identity Repo
%% LOGIN FLOW
    rect rgb(230, 245, 255)
        Note over Client, UserDB: Login Process
        Client ->> Router: POST /auth/login/password<br/>{email, password}
        Router ->> Auth: authenticate_with_password(email, password)
        Auth ->> UserDB: find_auth_identity_by_provider_subject()
        UserDB -->> Auth: return identity
        Auth ->> Auth: verify_password(submitted, stored_hash)
        Auth ->> UserDB: get_user(identity.user_id)
        UserDB -->> Auth: return user
        Auth ->> Auth: assert user.status == ACTIVE
        Auth ->> JWT: create_access_token(user_id)
        JWT -->> Auth: return access_jwt (stateless, 30m TTL)
        Auth ->> JWT: create_refresh_token(user_id)
        JWT -->> Auth: return refresh_jwt (7d TTL, unique jti)
        Auth ->> Auth: hash = SHA256(refresh_jwt)
        Auth ->> DB: create_refresh_token(hash, expires_at)
        DB -->> Auth: stored
        Auth -->> Router: return TokenPair(access, refresh)
        Router -->> Client: 200 OK {access_token, refresh_token}
    end
```
