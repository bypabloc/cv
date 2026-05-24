"""Service save_tracking_event — escritura del row en Neon.

Given un payload de tracking con event_id y event_type_id,
When save_tracking_event escribe la fila,
Then `insert_tracking` recibe un payload con session_id, page_id (uuid7
     generado), event_id, event_type_id y el resto del enrichment.

Spec direct-neon-writes: el Lambda escribe directo a Neon (no a
DynamoDB). Mockeamos `insert_tracking` y verificamos el payload exacto.
"""

import pytest

from tests.unit._helpers import EVENT_ID, EVENT_TYPE_ID, SESSION_ID

pytestmark = pytest.mark.unit


def test_save_tracking_event_persists_item(
    mock_neon_writes: list[dict], tracking_aws: None
) -> None:
    from services.tracking_service import save_tracking_event

    # Act
    result = save_tracking_event(
        {
            'session_id': SESSION_ID,
            'event_id': EVENT_ID,
            'event_type_id': EVENT_TYPE_ID,
            'page_url': 'https://the-full-stack.com/',
        }
    )

    # Assert: una sola fila se escribio
    assert len(mock_neon_writes) == 1
    payload = mock_neon_writes[0]
    assert payload['session_id'] == SESSION_ID
    assert payload['event_id'] == EVENT_ID
    assert payload['event_type_id'] == EVENT_TYPE_ID
    assert payload['page_url'] == 'https://the-full-stack.com/'
    # page_id se genera dentro del service (UUIDv7)
    assert payload['page_id'] == result['page_id']
    # stream_event_id queda en None (campo legacy del stream)
    assert payload['stream_event_id'] is None
    # expires_at: None — Neon no usa TTL (es analytics, no cache)
    assert payload['expires_at'] is None
