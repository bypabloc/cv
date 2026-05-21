"""Controller tracking/track — payload invalido en la fase validate.

Given un evento sin session_id (campo requerido del modelo),
When el controller Track ejecuta su ciclo run(),
Then la fase validate falla con code VALIDATION_ERROR y NO ejecuta.
"""

import pytest

pytestmark = pytest.mark.unit


def test_track_controller_rejects_invalid_payload(tracking_aws: None):
    from controllers.tracking.track import Track
    from settings.config import ErrorCode

    # Arrange: falta session_id -> TrackEventModel rechaza el payload.
    event = {
        'event_id': 'a1b2c3d4e5f60718293a4b5c6d7e8f90',
        'event_type_id': '019e372b-e0a7-7154-8279-8829bcf6a08c',
        'page_url': 'https://the-full-stack.com/',
        'meta': {'ip': '1.2.3.4', 'country': 'CL', 'user_agent': 'UA'},
    }

    # Act
    result = Track(event=event).run()

    # Assert
    assert result['is_valid'] is False
    assert result['code'] == ErrorCode.VALIDATION_ERROR.value
