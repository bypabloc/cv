"""Handler — sync legacy devuelve 204 y persiste a Neon.

Given ASYNC_MODE=false,
When un body /track valido entra,
Then comportamiento identico al pre-refactor: HTTP 204 No Content con
     body vacio Y la fila escrita en Neon (sync path).

AC-18 del plan lambdas-async-sqs (rollback de emergencia preserva el
flujo legacy).
"""

import pytest

from tests.unit._helpers import api_gw_event, lambda_context, valid_body

pytestmark = pytest.mark.unit


def test_handler_returns_204_in_sync_mode_legacy(
    sync_mode: None,
    mock_neon_writes: list[dict],
    tracking_aws: None,
) -> None:
    import handler

    # Arrange
    event = api_gw_event(body=valid_body())

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert: HTTP 204 con body vacio (fire-and-forget legacy).
    assert response['statusCode'] == 204
    assert response['body'] == ''
    # La persistencia llego a Neon en la misma invocacion.
    assert len(mock_neon_writes) == 1
