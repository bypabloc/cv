"""Controller Write — persiste 1 evento en una db_session.

Given un evento valido (el data del invoke async),
When Write.run() lo procesa,
Then abre UNA db_session y llama process_tracking_message con esa session
     y el modelo validado, devolviendo is_valid + inserted=True.
"""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from tests.unit._helpers import valid_body

pytestmark = pytest.mark.unit


def test_write_controller_persists_event() -> None:
    from controllers.writer.write import Write

    # Arrange: el controller recibe el `data` (no {operation,action,data}).
    data = valid_body(0)

    fake_session = MagicMock()

    @contextmanager
    def _fake_db_session():
        yield fake_session

    with (
        patch('controllers.writer.write.db_session', _fake_db_session),
        patch(
            'controllers.writer.write.process_tracking_message',
            return_value=True,
        ) as mock_process,
    ):
        # Act
        result = Write(event=data).run()

    # Assert
    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['inserted'] is True
    assert result['data']['page_id'] == data['page_id']
    # 1 sola llamada, con la session abierta por el controller.
    assert mock_process.call_count == 1
    assert mock_process.call_args.args[0] is fake_session
    assert mock_process.call_args.args[1].session_id == data['session_id']
