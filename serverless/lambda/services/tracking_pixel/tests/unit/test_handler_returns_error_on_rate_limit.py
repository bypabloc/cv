"""Handler — rate-limit agotado.

Given un evento valido pero el rate-limit lanza RateLimitExceededError,
When lambda_handler lo procesa,
Then devuelve HTTP 429 con code RATE_LIMIT_EXCEEDED (error_response).
"""

import json
from unittest.mock import patch

import pytest

from tests.unit._helpers import api_gw_event, lambda_context, valid_body

pytestmark = pytest.mark.unit


def test_handler_returns_error_on_rate_limit(tracking_aws: None):
    import handler
    from shared.rate_limit.exceptions import RateLimitExceededError

    # Arrange
    event = api_gw_event(body=valid_body())
    rate_error = RateLimitExceededError(
        'rate limit agotado', code='RATE_LIMIT_EXCEEDED'
    )

    # Act: el rate-limit (E/S externa) se mockea para forzar el rechazo.
    with patch(
        'controllers.tracking.track.check_or_raise',
        side_effect=rate_error,
    ):
        response = handler.lambda_handler(event, lambda_context())

    # Assert
    assert response['statusCode'] == 429
    assert json.loads(response['body'])['code'] == 'RATE_LIMIT_EXCEEDED'
