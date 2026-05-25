"""E2E — event_props (dict libre) se persiste como Map en DynamoDB.

Given un evento API Gateway con un event_props que trae datos
  especificos del tipo de evento (href, scroll depth, flag),
When lambda_handler lo procesa end-to-end,
Then devuelve HTTP 204 y el item persistido contiene el event_props
  completo con sus claves y valores.
"""

import pytest

from tests.integration._fixtures._builders import (
    api_gw_event,
    lambda_context,
    scan_tracking,
    valid_body,
)

pytestmark = pytest.mark.integration


def test_event_props_persisted_e2e():
    import handler

    # Arrange: event_props con un string, un numero y un booleano.
    props = {
        'href': 'https://the-full-stack.com/contact',
        'scroll_depth': 75,
        'above_fold': True,
    }
    event = api_gw_event(body=valid_body(event_props=props))

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert
    assert response['statusCode'] == 204
    items = scan_tracking()
    assert len(items) == 1
    persisted = items[0]['event_props']
    assert persisted['href'] == 'https://the-full-stack.com/contact'
    assert int(persisted['scroll_depth']) == 75
    assert persisted['above_fold'] is True
