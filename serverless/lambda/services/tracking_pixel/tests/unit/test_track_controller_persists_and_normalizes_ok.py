"""Controller tracking/track — caso exitoso.

Given un evento de tracking valido y el rate-limit por debajo del limite,
When el controller Track ejecuta su ciclo run(),
Then persiste el evento y devuelve {is_valid: True, code: 0, status: ok}.
"""

import pytest

from tests.unit._helpers import valid_body

pytestmark = pytest.mark.unit


def test_track_controller_persists_and_normalizes_ok(
    sync_mode: None,
    mock_neon_writes: list[dict],
    tracking_aws: None,
) -> None:
    from controllers.tracking.track import Track

    # Arrange
    event = {
        **valid_body(),
        'meta': {'ip': '1.2.3.4', 'country': 'CL', 'user_agent': 'UA'},
    }
    controller = Track(event=event)

    # Act
    result = controller.run()

    # Assert: respuesta normalizada
    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['operation'] == 'tracking'
    assert result['data']['action'] == 'track'
    assert result['data']['status'] == 'ok'
    assert result['data']['session_id'] == valid_body()['session_id']
    # Assert: la persistencia llego a Neon (mockeada)
    assert len(mock_neon_writes) == 1
