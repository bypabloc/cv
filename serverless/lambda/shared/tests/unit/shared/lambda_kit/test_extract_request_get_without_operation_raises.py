"""shared.lambda_kit.http_dispatch.extract_request — error.

Given un evento GET sin el query param 'operation',
When se procesa con extract_request,
Then levanta ValidationError con code='INVALID_REQUEST'.
"""

from __future__ import annotations

import pytest
from shared.core.exceptions import ValidationError
from shared.lambda_kit import extract_request

pytestmark = pytest.mark.unit


def test_extract_request_get_without_operation_raises() -> None:
    # Arrange
    event = {
        'httpMethod': 'GET',
        'queryStringParameters': {'action': 'get'},
    }

    # Act
    with pytest.raises(ValidationError) as exc_info:
        extract_request(event)

    # Assert
    assert exc_info.value.code == 'INVALID_REQUEST'


def test_extract_request_get_without_action_raises() -> None:
    """Given GET sin 'action', Then ValidationError INVALID_REQUEST."""
    # Arrange
    event = {
        'httpMethod': 'GET',
        'queryStringParameters': {'operation': 'cv'},
    }

    # Act
    with pytest.raises(ValidationError) as exc_info:
        extract_request(event)

    # Assert
    assert exc_info.value.code == 'INVALID_REQUEST'


def test_extract_request_get_without_query_params_raises() -> None:
    """Given GET sin queryStringParameters, Then ValidationError."""
    # Arrange
    event = {'httpMethod': 'GET', 'queryStringParameters': None}

    # Act
    with pytest.raises(ValidationError) as exc_info:
        extract_request(event)

    # Assert
    assert exc_info.value.code == 'INVALID_REQUEST'
