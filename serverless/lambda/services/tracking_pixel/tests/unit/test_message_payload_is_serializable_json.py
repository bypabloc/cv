"""Service enqueue_tracking_message — payload SQS round-trips por JSON.

Given un evento /track con datetime + UUIDs + dict event_props,
When `enqueue_tracking_message` arma el payload,
Then `json.dumps(payload, default=str)` no lanza excepcion Y
     `json.loads(...)` re-construye el mismo dict (con `datetime` ya
     serializado a ISO 8601). Esto garantiza que SQS no rechazara el
     mensaje y que el worker podra deserializarlo sin sorpresas.
"""

import json
from datetime import UTC, datetime

import pytest

from tests.unit._helpers import CHROME_UA, EVENT_ID, EVENT_TYPE_ID, SESSION_ID

pytestmark = pytest.mark.unit


def test_message_payload_is_serializable_json(
    captured_queue: list[dict],
    tracking_aws: None,
) -> None:
    from services.tracking_service import enqueue_tracking_message

    # Arrange
    page_id = '019e5c50-0000-7000-8000-aaaaaaaaaaaa'
    created_at = datetime(2026, 5, 25, 12, 30, 45, tzinfo=UTC)
    validated_input = {
        'session_id': SESSION_ID,
        'event_id': EVENT_ID,
        'event_type_id': EVENT_TYPE_ID,
        'page_url': 'https://the-full-stack.com/projects',
        'page_path': '/projects',
        'page_title': 'Projects',
        'viewport_width': 1280,
        'viewport_height': 800,
        'device_pixel_ratio': 2.0,
        'utm_source': 'twitter',
        'utm_medium': 'social',
        'utm_campaign': 'launch',
        'utm_content': '',
        'utm_term': None,
        'referrer': 'https://twitter.com/',
        'niche': 'fintech',
        'event_props': {'href': 'https://x.com', 'scroll_pct': 75},
    }

    # Act
    enqueue_tracking_message(
        page_id=page_id,
        created_at=created_at,
        validated_input=validated_input,
        ip='1.2.3.4',
        user_agent=CHROME_UA,
        country='CL',
    )

    # Assert: el publisher recibio kwargs con el payload listo.
    assert len(captured_queue) == 1
    sent_payload = captured_queue[0]['payload']

    # round-trip: dumps + loads no rompe.
    serialized = json.dumps(sent_payload, default=str)
    deserialized = json.loads(serialized)

    # Valores criticos sobreviven la serializacion.
    assert deserialized['page_id'] == page_id
    assert deserialized['session_id'] == SESSION_ID
    assert deserialized['event_id'] == EVENT_ID
    assert deserialized['event_type_id'] == EVENT_TYPE_ID
    assert deserialized['created_at'] == '2026-05-25T12:30:45+00:00'
    assert deserialized['event_props'] == {
        'href': 'https://x.com',
        'scroll_pct': 75,
    }
    assert deserialized['schema_version'] == 1
    assert deserialized['ip'] == '1.2.3.4'
    assert deserialized['country'] == 'CL'
    assert deserialized['user_agent'] == CHROME_UA
