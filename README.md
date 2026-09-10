# FastAPI Auth Lib

![Tests](https://github.com/zola8/fastapi-auth-lib/actions/workflows/tests.yml/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.13-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**fastapi-auth-lib** is a lightweight authentication and authorization library for FastAPI applications.

Features:

- Easy integration with FastAPI
- Ready-made components (like Spring Framework)

## Installation

### Prerequisites

- Python 3.13+
- FastAPI 0.141+

### Install dependencies

```shell
pip install -r requirements.txt
```

If you are a developer, install dev dependencies:

```shell
pip install -r requirements-dev.txt
```

## Examples

For documentations see:

- [Registration with Activation](examples/docs/Registration%20with%20Activation.md)
- [Forgot Password](examples/docs/Forgot%20Password.md)
- [Resend Activation](examples/docs/Resend%20Activation.md)
- [Login](examples/docs/Login.md)
- [Logout](examples/docs/Logout.md)

For examples see the **/examples** folder.

For test coverage, use:

```shell
pytest --cov-reset --cov=src/fastapi_auth_lib --cov-report=html
```

For test application: [fastapi-auth-lib-react-test](https://github.com/zola8/fastapi-auth-lib-react-test)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

PyPi repository: [fastapi-auth-lib-zo](https://pypi.org/project/fastapi-auth-lib-zo/)
(I had to change because of naming conventions.)

------

> Hello everyone,
>
> I am Zoltán, the author of this authentication library. I know it's far from perfect and still lacks many features.
> However, I wanted to create a demo - illustrating that the Pythonic approach can be just as straightforward as
> using a Java Spring library.
>
> I hope you find it helpful. I'll stop here unless there's a request to continue.


Made with ❤️ for the FastAPI community

by Zoltán M © 2026
