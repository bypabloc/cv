"""shared.db.repository.is_event_processed.

Given un event_id que ya esta en processed_stream_events,
When se invoca is_event_processed,
Then devuelve True.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from shared.db.repository import is_event_processed

pytestmark = pytest.mark.unit


def test_is_event_processed_true_when_row_exists() -> None:
    # Arrange
    session = MagicMock()
    session.execute.return_value.first.return_value = ('evt-123',)

    # Act
    result = is_event_processed(session, 'evt-123')

    # Assert
    assert result is True
