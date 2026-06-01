"""Handler — evento valido se persiste y devuelve el resultado.

Given un evento {operation,action,data} valido y la persistencia OK (mock),
When lambda_handler procesa el invoke,
Then devuelve el data del controller (con inserted=True).
"""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from tests.unit._helpers import lambda_context, write_event

pytestmark = pytest.mark.unit


def test_handler_writes_event_ok() -> None:
    import handler

    # Arrange: persistencia OK (mock del service).
    event = write_event(0)

    fake_session = MagicMock()

    @contextmanager
    def _fake_db_session():
        yield fake_session

    with (
        patch('controllers.writer.write.db_session', _fake_db_session),
        patch(
            'controllers.writer.write.process_tracking_message',
            return_value=True,
        ),
    ):
        # Act
        result = handler.lambda_handler(event, lambda_context())

    # Assert
    assert result['inserted'] is True
    assert result['page_id'] == event['data']['page_id']
    assert result['operation'] == 'tracking'
    assert result['action'] == 'write'
