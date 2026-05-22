"""Handler — el evento no resuelve a un controller.

Given un batch con records y un run_controller que devuelve stage
     'validation' (no se resolvio el controller),
When lambda_handler lo procesa,
Then reporta TODOS los records como batchItemFailures (AWS reintenta).
"""

from unittest.mock import patch

import pytest

from tests.unit._helpers import contact_record, lambda_context, stream_event

pytestmark = pytest.mark.unit


def test_handler_reports_all_failed_on_validation_stage():
    import handler
    from shared.lambda_kit.dispatch import DispatchResult

    # Arrange
    event = stream_event(contact_record('evt-1'))
    validation_fail = DispatchResult(
        is_valid=False,
        data={'message': 'operacion invalida'},
        code=1001,
        stage='validation',
    )
    with patch.object(
        handler, 'run_controller', return_value=validation_fail
    ):
        # Act
        result = handler.lambda_handler(event, lambda_context())

    # Assert
    assert result == {
        'batchItemFailures': [{'itemIdentifier': 'evt-1'}],
    }
