"""Service save_tracking_event — escritura del row en Neon.

Given un payload de tracking con event_id y event_type_id,
When save_tracking_event escribe la fila,
Then `insert_tracking` recibe un payload con session_id, visit_id
     (devuelto por el helper mockeado), page_id (uuid7 generado),
     event_id, event_type_id y el resto del enrichment.

Spec sessions-normalize: el service UPSERTea session + visit via el
helper y luego inserta tracking_events con `visit_id`. Mockeamos
`ensure_session_and_visit` + `insert_tracking` y verificamos el SHAPE
del payload de tracking_events.

Las 12 columnas dropeadas (ip/country/ua/browser*/os/device_type +
5 utm_*) NO deben estar en el payload del tracking_event — viven en
sessions/session_visits.
"""

import pytest

from tests.unit._helpers import EVENT_ID, EVENT_TYPE_ID, SESSION_ID

pytestmark = pytest.mark.unit

# Debe coincidir con _STUB_VISIT_ID del conftest.
_STUB_VISIT_ID = '019e5c50-0000-7000-8000-000000000001'


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
            'page_path': '/',
            'niche': 'hub',
        }
    )

    # Assert: una sola fila tracking_events se escribio
    assert len(mock_neon_writes) == 1
    payload = mock_neon_writes[0]
    assert payload['session_id'] == SESSION_ID
    assert payload['visit_id'] == _STUB_VISIT_ID
    assert payload['event_id'] == EVENT_ID
    assert payload['event_type_id'] == EVENT_TYPE_ID
    # page_id se genera dentro del service (UUIDv7)
    assert payload['page_id'] == result['page_id']
    # result devuelve session_id + page_id + visit_id (nuevo en spec).
    assert result['session_id'] == SESSION_ID
    assert result['visit_id'] == _STUB_VISIT_ID

    # Columnas viejas que YA NO van en tracking_events:
    # (spec drop-cloudfront-meta)
    assert 'expires_at' not in payload
    assert 'cloudfront_meta' not in payload
    assert 'page_url' not in payload
    assert 'page_title' not in payload
    assert 'referrer' not in payload
    # (spec sessions-normalize: movidas a sessions/session_visits)
    assert 'ip' not in payload
    assert 'country' not in payload
    assert 'user_agent' not in payload
    assert 'browser' not in payload
    assert 'browser_version' not in payload
    assert 'os' not in payload
    assert 'device_type' not in payload
    assert 'utm_source' not in payload
    assert 'utm_medium' not in payload
    assert 'utm_campaign' not in payload
    assert 'utm_content' not in payload
    assert 'utm_term' not in payload
