import asyncio

from src.fastapi_auth_lib.services.password_hasher.argon2_hasher import Argon2PasswordHasher
from src.fastapi_auth_lib.services.password_hasher.bcrypt_hasher import BCryptPasswordHasher
from src.fastapi_auth_lib.services.service_factory import AuthServiceBuilder


async def main() -> None:
    # Default: Argon2id + in-memory repos
    service = AuthServiceBuilder().build()
    user = await service.register("user@email.com", "test123")
    print(f"Registered (argon2): {user.user_id} | {user.email}")

    # Custom Argon2 with higher memory cost
    service2 = (
        AuthServiceBuilder()
        .with_password_hasher(Argon2PasswordHasher(memory_cost=131072))
        .build()
    )
    user2 = await service2.register("user2@email.com", "securepass")
    print(f"Registered (custom argon2): {user2.user_id} | {user2.email}")

    # Swap to bcrypt
    service3 = (
        AuthServiceBuilder()
        .with_password_hasher(BCryptPasswordHasher(rounds=14))
        .build()
    )
    user3 = await service3.register("user3@email.com", "anotherpass")
    print(f"Registered (bcrypt): {user3.user_id} | {user3.email}")

    # Authenticate
    authenticated = await service.authenticate("user@email.com", "test123")
    print(f"Authenticated: {authenticated.email}")


if __name__ == "__main__":
    asyncio.run(main())
