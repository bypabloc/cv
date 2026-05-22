"""shared.db.repository.is_event_processed.

Given un event_id que NO esta en processed_stream_events,
When se invoca is_event_processed,
Then devuelve False.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from shared.db.repository import is_event_processed

pytestmark = pytest.mark.unit


def test_is_event_processed_false_when_absent() -> None:
    # Arrange
    session = MagicMock()
    session.execute.return_value.first.return_value = None

    # Act
    result = is_event_processed(session, 'evt-404')

    # Assert
    assert result is False
