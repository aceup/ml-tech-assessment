"""
Unit tests for custom exception classes.

Tests cover exception instantiation, message formatting, status codes,
and details parameter handling for all custom exceptions.
"""

import pytest
from fastapi import status

from app.utils.exceptions import (
    AppException,
    ExternalServiceException,
    NotFoundException,
    ValidationException,
)


# ============================================================================
# AppException Tests (2 tests)
# ============================================================================


def test_app_exception_creates_with_message():
    """
    Test that AppException creates with message and default status code.

    Arrange & Act: Create AppException with message
    Assert: Message is stored, default status code is 500, details is None
    """
    # Arrange
    message = "An error occurred"

    # Act
    exc = AppException(message=message)

    # Assert
    assert exc.message == message
    assert str(exc) == message
    assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc.details is None
    assert isinstance(exc, Exception)


def test_app_exception_includes_details_dict():
    """
    Test that AppException stores details parameter.

    Arrange & Act: Create AppException with details dict
    Assert: Details are stored and accessible
    """
    # Arrange
    message = "An error occurred"
    details = {"error_code": "ERR001", "context": "test_context"}

    # Act
    exc = AppException(message=message, details=details)

    # Assert
    assert exc.message == message
    assert exc.details == details
    assert exc.details["error_code"] == "ERR001"
    assert exc.details["context"] == "test_context"
    assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# ============================================================================
# NotFoundException Tests (2 tests)
# ============================================================================


def test_not_found_exception_with_resource_and_id():
    """
    Test NotFoundException formats message with resource and identifier.

    Arrange & Act: Create NotFoundException with resource and identifier
    Assert: Message includes resource name and identifier in proper format
    """
    # Arrange
    resource = "Analysis"
    identifier = "abc-123"

    # Act
    exc = NotFoundException(resource=resource, identifier=identifier)

    # Assert
    assert "Analysis" in exc.message
    assert "abc-123" in exc.message
    assert exc.message == f"{resource} with id '{identifier}' not found"
    assert str(exc) == f"{resource} with id '{identifier}' not found"
    assert exc.details["resource"] == resource
    assert exc.details["identifier"] == identifier


def test_not_found_exception_has_404_status_code():
    """
    Test that NotFoundException has correct 404 status code.

    Arrange & Act: Create NotFoundException
    Assert: Status code is 404 (Not Found)
    """
    # Arrange & Act
    exc = NotFoundException(resource="User", identifier="user-456")

    # Assert
    assert exc.status_code == status.HTTP_404_NOT_FOUND
    assert exc.status_code == 404
    assert isinstance(exc, AppException)


# ============================================================================
# ValidationException Tests (2 tests)
# ============================================================================


def test_validation_exception_with_message():
    """
    Test ValidationException stores custom validation message.

    Arrange & Act: Create ValidationException with custom message
    Assert: Message and optional details are stored correctly
    """
    # Arrange
    message = "Email format is invalid"
    details = {"field": "email", "constraint": "valid_email"}

    # Act
    exc = ValidationException(message=message, details=details)

    # Assert
    assert exc.message == message
    assert str(exc) == message
    assert exc.details == details
    assert exc.details["field"] == "email"
    assert exc.details["constraint"] == "valid_email"


def test_validation_exception_has_422_status_code():
    """
    Test that ValidationException has correct 422 status code.

    Arrange & Act: Create ValidationException
    Assert: Status code is 422 (Unprocessable Entity)
    """
    # Arrange & Act
    exc = ValidationException(message="Invalid input data")

    # Assert
    assert exc.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert exc.status_code == 422
    assert isinstance(exc, AppException)


# ============================================================================
# ExternalServiceException Tests (2 tests)
# ============================================================================


def test_external_service_exception_with_service_name():
    """
    Test ExternalServiceException formats message with service name.

    Arrange & Act: Create ExternalServiceException with service and message
    Assert: Message includes service name and error message in correct format
    """
    # Arrange
    service = "OpenAI"
    message = "Rate limit exceeded"
    details = {"retry_after": 60, "error_code": "rate_limit_exceeded"}

    # Act
    exc = ExternalServiceException(service=service, message=message, details=details)

    # Assert
    assert exc.message == f"{service} error: {message}"
    assert "OpenAI" in exc.message
    assert "Rate limit exceeded" in exc.message
    assert exc.details["service"] == service
    assert exc.details["retry_after"] == 60
    assert exc.details["error_code"] == "rate_limit_exceeded"


def test_external_service_exception_has_502_status_code():
    """
    Test that ExternalServiceException has correct 502 status code.

    Arrange & Act: Create ExternalServiceException
    Assert: Status code is 502 (Bad Gateway)
    """
    # Arrange & Act
    exc = ExternalServiceException(
        service="ThirdPartyAPI", message="Connection timeout"
    )

    # Assert
    assert exc.status_code == status.HTTP_502_BAD_GATEWAY
    assert exc.status_code == 502
    assert isinstance(exc, AppException)


# ============================================================================
# Integration Tests - Exception Hierarchy (Implicit in above tests)
# ============================================================================
# All custom exceptions inherit from AppException, verified by isinstance checks


@pytest.mark.parametrize(
    "exception_class,resource,expected_status",
    [
        (NotFoundException, "Test", status.HTTP_404_NOT_FOUND),
        (ValidationException, None, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (ExternalServiceException, "Service", status.HTTP_502_BAD_GATEWAY),
    ],
)
def test_all_exceptions_inherit_from_app_exception(
    exception_class, resource, expected_status
):
    """
    Test that all custom exceptions inherit from AppException.

    Parametrized test to verify inheritance and status codes.
    """
    # Arrange & Act
    if exception_class == NotFoundException:
        exc = exception_class(resource=resource, identifier="test-id")
    elif exception_class == ValidationException:
        exc = exception_class(message="Test error")
    else:  # ExternalServiceException
        exc = exception_class(service=resource, message="Test error")

    # Assert
    assert isinstance(exc, AppException)
    assert isinstance(exc, Exception)
    assert exc.status_code == expected_status
    assert hasattr(exc, "message")
    assert hasattr(exc, "details")
