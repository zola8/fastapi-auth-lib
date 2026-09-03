# FastAPI Auth Lib Logging Example

Simple logging configuration example using `fastapi_auth_lib`.

## Example 01

Without `configure_logging()`:

```
INFO:__main__:hello info logging!
```

With `configure_logging()`:

```
2026-08-16 18:56:50 | INFO     | __main__:10 | hello info logging!
```

## Example 02

Simple logging configuration example using `fastapi_auth_lib` with JSON format output.

```
configure_logging(log_format=LogFormat.PROD)
```

With `configure_logging(log_format=LogFormat.PROD)`:

```json
{"asctime": "2026-08-17 08:31:36,769", "levelname": "INFO", "name": "__main__", "message": "hello info logging!"}
```
