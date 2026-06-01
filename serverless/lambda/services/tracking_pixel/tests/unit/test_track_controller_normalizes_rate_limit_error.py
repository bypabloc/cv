"""Controller tracking/track — rate-limit agotado.

Given un evento valido pero el rate-limit lanza RateLimitExceededError,
When el controller Track ejecuta su ciclo run(),
Then devuelve {is_valid: False, code: 4001} con la ApplicationError en data.
"""

from unittest.mock import patch

import pytest

from tests.unit._helpers import valid_body

pytestmark = pytest.mark.unit


def test_track_controller_normalizes_rate_limit_error(tracking_aws: None):
    from controllers.tracking.track import Track
    from settings.config import ErrorCode
    from shared.rate_limit.exceptions import RateLimitExceededError

    # Arrange
    event = {
        **valid_body(),
        'meta': {'ip': '9.9.9.9', 'country': 'CL', 'user_agent': 'UA'},
    }
    rate_error = RateLimitExceededError(
        'rate limit agotado', code='RATE_LIMIT_EXCEEDED'
    )

    # Act: el rate-limit (E/S externa) se mockea para forzar el rechazo.
    with patch(
        'controllers.tracking.track.check_or_raise',
        side_effect=rate_error,
    ):
        result = Track(event=event).run()

    # Assert
    assert result['is_valid'] is False
    assert result['code'] == ErrorCode.RATE_LIMITED.value
    assert result['data']['error_code'] == 'RATE_LIMIT_EXCEEDED'
    assert result['data']['application_error'] is rate_error
