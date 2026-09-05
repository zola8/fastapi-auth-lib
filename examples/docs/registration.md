# Step-by-Step Registration Workflow with Activation

**1. User Input (Frontend):** The user enters an email address and a password into the sign-up form.

**2. Data Validation (Backend/Frontend):** The system checks if the email format is valid and ensures the password meets security rules (e.g., minimum/maximum lengths).

**3. Uniqueness Check (Backend):** The server queries the database to confirm the email is not already registered.

**4. Password Hashing (Backend):** The system securely hashes the password using a strong algorithm like bcrypt or Argon2. It never stores plain text.

**5. Account Creation & Token Generation (Backend):** A new user record is saved with a status of inactive. A unique, time-limited verification token or one-time code is generated and saved.

**6. Verification Dispatch (Backend):** An email service sends a confirmation link or code containing the unique token to the user's provided email address.

**7. Account Activation (Verification):** The user clicks the link or enters the code, the server validates the token against the database, updates the user status to active, and logs the user in.


```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend as FastAPI Backend
    participant Database
    participant EmailService

    User->>Frontend: Enter email & password
    Frontend->>Backend: POST /register/password
    Backend->>Backend: Validate input (Pydantic)
    Backend->>Database: Check if email exists
    Database-->>Backend: Result

    alt Email already exists
        Backend-->>Frontend: 400 DUPLICATE error
        Frontend-->>User: Show error
    else Email is unique
        Backend->>Backend: Hash password (bcrypt)
        Backend->>Database: Create user (status=INACTIVE)
        Database-->>Backend: User created
        Backend->>Database: Create auth identity (password hash)
        Database-->>Backend: Identity created
        Backend->>Backend: Generate verification (activation) token
        Backend->>Database: Store token (user or token table)
        Backend->>EmailService: Send verification email with token
        EmailService-->>User: Deliver email
        Backend-->>Frontend: 201 Created (user info)
        Frontend-->>User: Show success message
    end

    User->>Frontend: Click activation link
    Frontend->>Backend: GET /activate?token=...
    Backend->>Database: Validate token
    Database-->>Backend: Token valid
    Backend->>Database: Update user status to ACTIVE
    Database-->>Backend: Updated
    Backend-->>Frontend: Verification success
    Frontend-->>User: Show activation success
```
