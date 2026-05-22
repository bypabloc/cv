"""Service stream_service.parse_tracking_record — INSERT de tracking.

Given un Stream record INSERT de la tabla tracking con session_id y
     page_id,
When se invoca parse_tracking_record,
Then devuelve un payload con los campos mapeados a TrackingEvent.
"""

import pytest

from tests.unit._helpers import tracking_record

pytestmark = pytest.mark.unit


def test_service_parses_tracking_image_to_payload():
    from services.stream_service import parse_tracking_record

    # Act
    payload = parse_tracking_record(tracking_record('evt-1'))

    # Assert
    assert payload is not None
    assert payload['session_id'] == 'sess-evt-1'
    assert payload['page_id'] == '019e372b-e0a7-7154-8279-8829bcf6a08c'
    assert payload['stream_event_id'] == 'evt-1'
    assert payload['page_url'] == 'https://the-full-stack.com/'
