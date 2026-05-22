"""Handler — el controller reporta is_valid False (caso defensivo).

Given un batch y un run_controller que devuelve stage 'controller' con
     is_valid False,
When lambda_handler lo procesa,
Then reporta TODOS los records como batchItemFailures (AWS reintenta).
"""

from unittest.mock import patch

import pytest

from tests.unit._helpers import contact_record, lambda_context, stream_event

pytestmark = pytest.mark.unit


def test_handler_reports_all_failed_when_controller_invalid():
    import handler
    from shared.lambda_kit.dispatch import DispatchResult

    # Arrange
    event = stream_event(contact_record('evt-1'))
    invalid = DispatchResult(
        is_valid=False,
        data={},
        code=6000,
        stage='controller',
    )
    with patch.object(handler, 'run_controller', return_value=invalid):
        # Act
        result = handler.lambda_handler(event, lambda_context())

    # Assert
    assert result == {
        'batchItemFailures': [{'itemIdentifier': 'evt-1'}],
    }
