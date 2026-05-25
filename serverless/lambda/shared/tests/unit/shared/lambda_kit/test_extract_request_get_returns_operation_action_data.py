"""shared.lambda_kit.http_dispatch.extract_request — GET.

Given un evento API Gateway con httpMethod GET y queryStringParameters
     que incluyen operation, action y otros parametros,
When se procesa con extract_request,
Then devuelve operation, action y data (con los parametros restantes).
"""

from __future__ import annotations

import pytest
from shared.lambda_kit import extract_request

pytestmark = pytest.mark.unit


def test_extract_request_get_returns_operation_action_data() -> None:
    # Arrange
    event = {
        'httpMethod': 'GET',
        'queryStringParameters': {
            'operation': 'cv',
            'action': 'experiences',
            'niche': 'fintech',
            'locale': 'es',
        },
    }

    # Act
    result = extract_request(event)

    # Assert
    assert result.operation == 'cv'
    assert result.action == 'experiences'
    assert result.data == {'niche': 'fintech', 'locale': 'es'}
    assert result.method == 'GET'
