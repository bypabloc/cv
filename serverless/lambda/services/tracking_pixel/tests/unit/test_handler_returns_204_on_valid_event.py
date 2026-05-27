"""Handler — evento de tracking valido en modo sync legacy.

Given un evento API Gateway con un body de tracking valido y ASYNC_MODE=false,
When lambda_handler lo procesa,
Then devuelve HTTP 204 No Content con body vacio (fire-and-forget) Y
     persiste a Neon en la misma invocacion (sync legacy).
"""

import pytest

from tests.unit._helpers import api_gw_event, lambda_context, valid_body

pytestmark = pytest.mark.unit


def test_handler_returns_204_on_valid_event(
    sync_mode: None,
    mock_neon_writes: list[dict],
    tracking_aws: None,
) -> None:
    import handler

    # Arrange
    event = api_gw_event(
        body=valid_body(
            page_title='Projects',
            utm_source='twitter',
            viewport_width=1920,
            niche='fintech',
        )
    )

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert
    assert response['statusCode'] == 204
    assert response['body'] == ''
    # La persistencia llego al repository (Neon mockeado)
    assert len(mock_neon_writes) == 1
