"""Controller tracking/track — rate-limit bloquea ANTES del encode.

Given ASYNC_MODE=true + el rate-limit lanza RateLimitExceededError,
When el controller Track ejecuta su ciclo run(),
Then devuelve {is_valid: False, code: RATE_LIMITED} Y `send_to_queue`
     NUNCA se invoca: el rate-limit corre ANTES del branch async/sync,
     asi una IP rate-limited NO genera trafico SQS.

AC-7 del plan lambdas-async-sqs.
"""

from unittest.mock import patch

import pytest

from tests.unit._helpers import valid_body

pytestmark = pytest.mark.unit


def test_rate_limit_failure_does_not_enqueue(
    async_mode: None,
    captured_queue: list[dict],
    tracking_aws: None,
) -> None:
    from controllers.tracking.track import Track
    from settings.config import ErrorCode
    from shared.rate_limit import RateLimitExceededError

    # Arrange
    event = {
        **valid_body(),
        'meta': {'ip': '9.9.9.9', 'country': 'CL', 'user_agent': 'UA'},
    }
    rate_error = RateLimitExceededError(
        'rate limit agotado', code='RATE_LIMIT_EXCEEDED'
    )

    # Act
    with patch(
        'controllers.tracking.track.check_or_raise',
        side_effect=rate_error,
    ):
        result = Track(event=event).run()

    # Assert: el controller normalizo el error.
    assert result['is_valid'] is False
    assert result['code'] == ErrorCode.RATE_LIMITED.value
    # NUNCA se publico nada a SQS.
    assert captured_queue == []
