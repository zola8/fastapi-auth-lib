import asyncio

from src.fastapi_auth_lib.core.exceptions import EntityNotFoundException
from src.fastapi_auth_lib.models.user import UserProfile
from src.fastapi_auth_lib.services.service_factory import UserServiceBuilder


async def main() -> None:
    service = UserServiceBuilder().build()

    # --- CREATE ---
    user = await service.create_user(
        UserProfile(email="alice@example.com", username="alice")
    )
    print(f"Created: {user.user_id} | {user.email} | status={user.status}")

    # --- GET BY ID ---
    fetched = await service.get_user(user.user_id)
    print(f"Fetched: {fetched.username} | roles={fetched.roles}")

    # --- GET MISSING (raises EntityNotFoundException) ---
    try:
        import uuid
        await service.get_user(uuid.uuid4())
    except EntityNotFoundException as exc:
        print(f"Not found (expected): {exc}")

    # --- LIST ALL ---
    all_users = await service.list_users()
    print(f"Total users: {len(all_users)}")

    # --- DELETE (soft) ---
    await service.delete_user(user.user_id)
    deleted = await service.get_user(user.user_id)
    print(f"After delete: status={deleted.status}")


if __name__ == "__main__":
    asyncio.run(main())
