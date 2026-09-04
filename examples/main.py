import uvicorn

from src.fastapi_auth_lib.api.app_builder import AppBuilder

app = (
    AppBuilder()
    .with_sql_services()
    .with_auth_router()
    .with_users_router()
    .with_admin_router()
    .with_exception_handlers()
    .build()
)

print(app)

if __name__ == '__main__':
    print("http://localhost:8080/docs")
    uvicorn.run(app, host="0.0.0.0", port=8080)
