"""Controller Write — INSERT idempotente (no-op) devuelve inserted=False.

Given un evento cuyo INSERT ya existia (process_tracking_message
     devuelve False = no-op por ON CONFLICT),
When Write.run() lo procesa,
Then is_valid=True (idempotencia != fallo) y data.inserted=False.
"""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from tests.unit._helpers import valid_body

pytestmark = pytest.mark.unit


def test_write_controller_idempotent_on_conflict() -> None:
    from controllers.writer.write import Write

    # Arrange: el INSERT es no-op (ya existia).
    data = valid_body(0)

    fake_session = MagicMock()

    @contextmanager
    def _fake_db_session():
        yield fake_session

    with (
        patch('controllers.writer.write.db_session', _fake_db_session),
        patch(
            'controllers.writer.write.process_tracking_message',
            return_value=False,
        ),
    ):
        # Act
        result = Write(event=data).run()

    # Assert: no-op NO es fallo.
    assert result['is_valid'] is True
    assert result['data']['inserted'] is False
