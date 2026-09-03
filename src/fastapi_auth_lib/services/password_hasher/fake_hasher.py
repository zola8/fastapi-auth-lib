class FakeHasher:
    def hash_password(self, password: str) -> str:
        return f"fake:{password}"

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return hashed_password == f"fake:{password}"
