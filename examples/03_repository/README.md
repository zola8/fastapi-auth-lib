# FastAPI Auth Lib

Lightweight authentication and authorization library for FastAPI applications.

## Example 01

The following example demonstrates basic user management operations using in-memory repositories.

**What This Code Does:**

1. Initializes Repositories:

    - Creates in-memory user and auth identity repositories for testing or development without a database.

2. Creates a User:

    - Builds a UserProfile with username and email
    - Saves it via create_user()
    - Returns the user with generated ID

3. Retrieves the User:

    - Fetches user by ID using get_user_by_id()
    - Confirms the user was stored successfully

4. Deletes the User:

    - Removes user with hard_delete=True (permanent deletion)
    - Soft delete available by omitting or setting hard_delete=False

5. Verifies Deletion:

    - Attempts to fetch deleted user
    - Catches EntityNotFoundException to confirm user is gone
    - Demonstrates proper error handling pattern

## Example 02

**What This Code Does:**

1. Creates a User Profile:

    - Builds a UserProfile with basic information (username, email)
    - Saves it to the user repository
    - Returns the user with generated user_id

2. Creates Authentication Identity:

    - Creates an AuthIdentity linked to the user via user_id
    - Specifies AuthProvider.PASSWORD indicating password-based authentication
    - Sets provider_subject to identify this specific credential
    - Stores password_hash (should be properly hashed in production)

3. Displays Results:

    - Prints the complete user profile
    - Prints the authentication identity record

**Key Concepts Demonstrated:**

- Separation of Concerns: User profile (who they are) vs. AuthIdentity (how they authenticate)
- Auth Method: A user can have only one identity (password)
- Provider Pattern: AuthProvider enum supports different authentication methods
- Repository Pattern: Clean data access for both users and credentials

## Example 03 - SQLAlchemy Async Repository Example

**Key Concepts Demonstrated:**

- Async Operations: All database operations are non-blocking using asyncio
- Session Management: Repository works within an async session scope
- Repository Pattern: Clean abstraction over SQLAlchemy operations
- CRUD Operations: Create, Read, Update, Delete (soft)
- Immutable Fields: Email cannot be changed after creation
- Role Management: Users can have multiple roles (USER, ADMIN)

## Example 04 - SQLAlchemy Sync Repository with Transaction Example

**Key Concepts Demonstrated:**

- Atomic Transactions: User and identity created together or not at all
- Session Management: Separate sessions for write and read operations
- Relationship Mapping: AuthIdentity linked to UserProfile via user_id
- Sync Operations: Blocking database calls (vs async alternative)
- Error Recovery: Proper rollback on failure to prevent partial data
