"""Controller tracking/track — encoder async no toca Neon.

Given ASYNC_MODE=true,
When el controller Track ejecuta su ciclo run() con un payload valido,
Then NINGUNA funcion de `shared.db.*` se invoca: ni `db_session`, ni
     `ensure_session_and_visit`, ni `insert_tracking`. La fixture
     `neon_off` reemplaza esas funciones por mocks que explotan si se
     llaman; el test pasa solo si el codigo ASYNC nunca las invoca.

AC-6 del plan lambdas-async-sqs (separacion encoder/worker: la
persistencia es responsabilidad del worker).
"""

import pytest

from tests.unit._helpers import valid_body

pytestmark = pytest.mark.unit


def test_async_mode_does_not_call_neon(
    async_mode: None,
    captured_queue: list[dict],
    neon_off: dict[str, int],
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

    # Assert: respuesta normalizada del encoder.
    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['status'] == 'accepted'
    # SQS recibio exactamente 1 mensaje.
    assert len(captured_queue) == 1
    # Ningun acceso a Neon (los mocks de neon_off explotan si se llaman).
    assert neon_off == {
        'db_session': 0,
        'ensure_session_and_visit': 0,
        'insert': 0,
    }
