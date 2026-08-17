from typing import List, Dict, Optional

from pydantic import BaseModel

from fastapi_auth_lib.api.schemas.responses import ApiResponse, ErrorDetail


class TestErrorDetail:
    """Test cases for ErrorDetail model."""

    def test_error_detail_required_fields(self):
        """Test ErrorDetail with only required fields."""
        error = ErrorDetail(
            code="VALIDATION_ERROR",
            message="Invalid input provided"
        )
        assert error.code == "VALIDATION_ERROR"
        assert error.message == "Invalid input provided"
        assert error.field is None
        assert error.value is None

    def test_error_detail_all_fields(self):
        """Test ErrorDetail with all fields populated."""
        error = ErrorDetail(
            code="INVALID_EMAIL",
            message="Email format is invalid",
            field="email",
            value="invalid-email"
        )
        assert error.code == "INVALID_EMAIL"
        assert error.message == "Email format is invalid"
        assert error.field == "email"
        assert error.value == "invalid-email"

    def test_error_detail_with_different_value_types(self):
        """Test ErrorDetail with various value types."""
        # String value
        error1 = ErrorDetail(
            code="TEST",
            message="Test error",
            field="name",
            value="John Doe"
        )
        assert error1.value == "John Doe"

        # Integer value
        error2 = ErrorDetail(
            code="TEST",
            message="Test error",
            field="age",
            value=25
        )
        assert error2.value == 25

        # List value
        error3 = ErrorDetail(
            code="TEST",
            message="Test error",
            field="items",
            value=[1, 2, 3]
        )
        assert error3.value == [1, 2, 3]

        # Dict value
        error4 = ErrorDetail(
            code="TEST",
            message="Test error",
            field="data",
            value={"key": "value"}
        )
        assert error4.value == {"key": "value"}

    def test_error_detail_field_optional(self):
        """Test that field is optional."""
        error = ErrorDetail(
            code="ERROR",
            message="Something went wrong"
        )
        assert error.field is None

        error_with_field = ErrorDetail(
            code="ERROR",
            message="Something went wrong",
            field="username"
        )
        assert error_with_field.field == "username"

    def test_error_detail_value_optional(self):
        """Test that value is optional."""
        error = ErrorDetail(
            code="ERROR",
            message="Something went wrong"
        )
        assert error.value is None

        error_with_value = ErrorDetail(
            code="ERROR",
            message="Something went wrong",
            value="invalid_input"
        )
        assert error_with_value.value == "invalid_input"

    def test_error_detail_serialization(self):
        """Test ErrorDetail serialization to dict."""
        error = ErrorDetail(
            code="NOT_FOUND",
            message="Resource not found",
            field="id",
            value=123
        )
        error_dict = error.model_dump()
        assert error_dict == {
            "code": "NOT_FOUND",
            "message": "Resource not found",
            "field": "id",
            "value": 123
        }

    def test_error_detail_deserialization(self):
        """Test ErrorDetail deserialization from dict."""
        data = {
            "code": "VALIDATION_ERROR",
            "message": "Invalid email",
            "field": "email",
            "value": "test"
        }
        error = ErrorDetail(**data)
        assert error.code == "VALIDATION_ERROR"
        assert error.message == "Invalid email"
        assert error.field == "email"
        assert error.value == "test"


class TestApiResponse:
    """Test cases for ApiResponse model."""

    def test_api_response_success_with_data(self):
        """Test successful response with data."""
        response = ApiResponse[str](
            success=True,
            data="Success message"
        )
        assert response.success is True
        assert response.data == "Success message"
        assert response.error is None

    def test_api_response_success_with_complex_data(self):
        """Test successful response with complex data types."""
        # Integer data
        response_int = ApiResponse[int](
            success=True,
            data=42
        )
        assert response_int.data == 42

        # List data
        response_list = ApiResponse[List[int]](
            success=True,
            data=[1, 2, 3]
        )
        assert response_list.data == [1, 2, 3]

        # Dict data
        response_dict = ApiResponse[Dict[str, str]](
            success=True,
            data={"name": "John", "email": "john@example.com"}
        )
        assert response_dict.data == {"name": "John", "email": "john@example.com"}

        # Nested data
        nested_data = {"user": {"id": 1, "name": "Alice"}, "count": 5}
        response_nested = ApiResponse[Dict](
            success=True,
            data=nested_data
        )
        assert response_nested.data == nested_data

    def test_api_response_success_with_custom_model(self):
        """Test successful response with custom model as data."""

        class User(BaseModel):
            id: int
            name: str
            email: str

        user = User(id=1, name="John Doe", email="john@example.com")
        response = ApiResponse[User](
            success=True,
            data=user
        )
        assert response.success is True
        assert response.data.id == 1
        assert response.data.name == "John Doe"
        assert response.data.email == "john@example.com"

    def test_api_response_failure_with_error(self):
        """Test failed response with error details."""
        error = ErrorDetail(
            code="AUTH_FAILED",
            message="Invalid credentials",
            field="password"
        )
        response = ApiResponse[None](
            success=False,
            data=None,
            error=error
        )
        assert response.success is False
        assert response.data is None
        assert response.error is not None
        assert response.error.code == "AUTH_FAILED"
        assert response.error.message == "Invalid credentials"
        assert response.error.field == "password"

    def test_api_response_failure_with_error_and_value(self):
        """Test failed response with error including invalid value."""
        error = ErrorDetail(
            code="INVALID_EMAIL",
            message="Email format is invalid",
            field="email",
            value="not-an-email"
        )
        response = ApiResponse[None](
            success=False,
            data=None,
            error=error
        )
        assert response.success is False
        assert response.data is None
        assert response.error.value == "not-an-email"

    def test_api_response_no_error_without_data(self):
        """Test ApiResponse with success True but no data (should be valid)."""
        response = ApiResponse[None](
            success=True,
            data=None,
            error=None
        )
        assert response.success is True
        assert response.data is None
        assert response.error is None

    def test_api_response_success_with_error_none(self):
        """Test that error can be None in successful response."""
        response = ApiResponse[str](
            success=True,
            data="Success"
        )
        assert response.error is None

    def test_api_response_optional_fields(self):
        """Test that data and error are optional."""
        # Only success required
        response = ApiResponse[None](
            success=True
        )
        assert response.success is True
        assert response.data is None
        assert response.error is None

    def test_api_response_serialization(self):
        """Test ApiResponse serialization to dict."""
        error = ErrorDetail(
            code="NOT_FOUND",
            message="User not found",
            field="user_id",
            value=999
        )
        response = ApiResponse[Optional[Dict]](
            success=False,
            data=None,
            error=error
        )
        response_dict = response.model_dump()
        assert response_dict == {
            "success": False,
            "data": None,
            "error": {
                "code": "NOT_FOUND",
                "message": "User not found",
                "field": "user_id",
                "value": 999
            }
        }

    def test_api_response_deserialization(self):
        """Test ApiResponse deserialization from dict."""
        data = {
            "success": True,
            "data": "Operation completed",
            "error": None
        }
        response = ApiResponse[str](**data)
        assert response.success is True
        assert response.data == "Operation completed"
        assert response.error is None

    def test_api_response_deserialization_with_error(self):
        """Test ApiResponse deserialization with error."""
        data = {
            "success": False,
            "data": None,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input",
                "field": "username",
                "value": "usr"
            }
        }
        response = ApiResponse[None](**data)
        assert response.success is False
        assert response.data is None
        assert response.error.code == "VALIDATION_ERROR"
        assert response.error.field == "username"

    def test_api_response_type_safety(self):
        """Test that ApiResponse maintains type safety."""
        # This should work with str
        response_str: ApiResponse[str] = ApiResponse[str](
            success=True,
            data="Hello"
        )
        assert isinstance(response_str.data, str)

        # This should work with int
        response_int: ApiResponse[int] = ApiResponse[int](
            success=True,
            data=123
        )
        assert isinstance(response_int.data, int)

        # This should work with list
        response_list: ApiResponse[List[str]] = ApiResponse[List[str]](
            success=True,
            data=["a", "b", "c"]
        )
        assert isinstance(response_list.data, list)

    def test_api_response_multiple_instances(self):
        """Test creating multiple ApiResponse instances with different types."""
        response1 = ApiResponse[str](
            success=True,
            data="Message"
        )
        response2 = ApiResponse[int](
            success=True,
            data=100
        )
        response3 = ApiResponse[bool](
            success=True,
            data=True
        )

        assert isinstance(response1.data, str)
        assert isinstance(response2.data, int)
        assert isinstance(response3.data, bool)

    def test_api_response_error_with_data_none(self):
        """Test error response with data explicitly set to None."""
        error = ErrorDetail(
            code="ERROR",
            message="Something went wrong"
        )
        response = ApiResponse[None](
            success=False,
            data=None,
            error=error
        )
        assert response.success is False
        assert response.data is None
        assert response.error is not None


class TestApiResponseIntegration:
    """Integration tests for ApiResponse usage patterns."""

    def test_api_response_as_function_return(self):
        """Test using ApiResponse as function return type."""

        def get_user(user_id: int) -> ApiResponse[Dict]:
            if user_id == 1:
                return ApiResponse[Dict](
                    success=True,
                    data={"id": 1, "name": "Alice"}
                )
            return ApiResponse[Dict](
                success=False,
                data=None,
                error=ErrorDetail(
                    code="USER_NOT_FOUND",
                    message=f"User {user_id} not found",
                    field="user_id",
                    value=user_id
                )
            )

        # Success case
        response = get_user(1)
        assert response.success is True
        assert response.data == {"id": 1, "name": "Alice"}
        assert response.error is None

        # Error case
        response = get_user(999)
        assert response.success is False
        assert response.data is None
        assert response.error.code == "USER_NOT_FOUND"
        assert response.error.value == 999

    def test_api_response_validation_scenario(self):
        """Test ApiResponse in a validation scenario."""

        def validate_email(email: str) -> ApiResponse[str]:
            if "@" not in email:
                return ApiResponse[str](
                    success=False,
                    data=None,
                    error=ErrorDetail(
                        code="INVALID_EMAIL",
                        message="Email must contain @",
                        field="email",
                        value=email
                    )
                )
            return ApiResponse[str](
                success=True,
                data="Email validated successfully"
            )

        # Invalid email
        response = validate_email("invalid-email")
        assert response.success is False
        assert response.error.code == "INVALID_EMAIL"
        assert response.error.value == "invalid-email"

        # Valid email
        response = validate_email("test@example.com")
        assert response.success is True
        assert response.data == "Email validated successfully"
