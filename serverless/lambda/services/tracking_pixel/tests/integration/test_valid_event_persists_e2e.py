"""E2E — evento de tracking valido persiste en DynamoDB.

Given un evento API Gateway con un body de tracking valido,
When lambda_handler lo procesa end-to-end (handler -> controller ->
  service -> persistencia),
Then devuelve HTTP 204 No Content y el evento queda persistido en la
  tabla DynamoDB tracking con los campos del payload.
"""

import pytest

from tests.integration._fixtures._builders import (
    EVENT_ID,
    EVENT_TYPE_ID,
    SESSION_ID,
    api_gw_event,
    lambda_context,
    scan_tracking,
    valid_body,
)

pytestmark = pytest.mark.integration


def test_valid_event_persists_e2e():
    import handler

    # Arrange
    event = api_gw_event(
        body=valid_body(
            page_title='Projects',
            utm_source='twitter',
            viewport_width=1920,
            viewport_height=1080,
            niche='fintech',
        )
    )

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert: respuesta HTTP 204 fire-and-forget.
    assert response['statusCode'] == 204
    assert response['body'] == ''

    # Assert: exactamente un item persistido con el payload completo.
    # Spec drop-cloudfront-meta: page_url, page_title, expires_at NO se
    # persisten (columnas dropeadas en alembic c3d4e5f6a7b8).
    items = scan_tracking()
    assert len(items) == 1
    item = items[0]
    assert item['session_id'] == SESSION_ID
    assert item['event_id'] == EVENT_ID
    assert item['event_type_id'] == EVENT_TYPE_ID
    assert item['utm_source'] == 'twitter'
    assert int(item['viewport_width']) == 1920
    assert int(item['viewport_height']) == 1080
    assert item['niche'] == 'fintech'
