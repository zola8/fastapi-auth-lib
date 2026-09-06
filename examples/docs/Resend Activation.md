# The "Resend Activation" Workflow

**1. User Request:** The user navigates to a "Resend Activation" or "Request New Token" page and enters their registered email address.

**2. Backend Validation:** The backend receives the request, validates the email, and checks if the associated account is in an inactive state.

**3. Token Generation & Invalidation:** The backend generates a new, time-limited (30 mins) activation token. For security, it invalidates any previously issued tokens for that account.

**4. Email Delivery:** The backend sends a new activation email to the user's address, containing a link with the fresh token.

**5. User Action:** The user receives the email and clicks the new activation link.

**6. Activation:** The backend validates the new token, activates the account, and marks the token as used (single-use).

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant EmailService

    User->>Frontend: Enters email and requests resend
    Frontend->>Backend: POST /resend-activation { email }
    Backend->>Backend: Validate email & check account inactive
    Backend->>Backend: Generate new token<br/>Invalidate old tokens
    Backend->>EmailService: Send activation email with new token
    EmailService-->>User: Deliver email (activation link)
    User->>Frontend: Clicks activation link (with token)
    Frontend->>Backend: POST /activate { token }
    Backend->>Backend: Validate token & activate account
    Backend-->>Frontend: Success response
    Frontend-->>User: Show activation success
```
