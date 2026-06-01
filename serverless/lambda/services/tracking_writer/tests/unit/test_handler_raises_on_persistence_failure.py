"""Handler — fallo de persistencia se RE-LANZA (AWS reintenta el invoke).

Given un evento valido pero process_tracking_message lanza,
When lambda_handler procesa el invoke,
Then RE-LANZA una excepcion (no se traga) para que AWS reintente el
     invoke async y, agotados los reintentos, lo mande a la DLQ.
"""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from tests.unit._helpers import lambda_context, write_event

pytestmark = pytest.mark.unit


def test_handler_raises_on_persistence_failure() -> None:
    import handler

    # Arrange: la persistencia lanza.
    event = write_event(0)

    fake_session = MagicMock()

    @contextmanager
    def _fake_db_session():
        yield fake_session

    def _raise(_session, _msg):
        msg = 'simulated neon failure'
        raise RuntimeError(msg)

    with (
        patch('controllers.writer.write.db_session', _fake_db_session),
        patch(
            'controllers.writer.write.process_tracking_message',
            side_effect=_raise,
        ),
        pytest.raises(Exception),  # noqa: B017 -- el handler re-lanza
    ):
        # Act / Assert
        handler.lambda_handler(event, lambda_context())
