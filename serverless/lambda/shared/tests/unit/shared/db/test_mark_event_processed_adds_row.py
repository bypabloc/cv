"""shared.db.repository.mark_event_processed.

Given una Session y un event_id procesado,
When se invoca mark_event_processed,
Then agrega a la Session una fila ProcessedStreamEvent con ese event_id,
     event_type y table_name.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from shared.db.models import ProcessedStreamEvent
from shared.db.repository import mark_event_processed

pytestmark = pytest.mark.unit


def test_mark_event_processed_adds_row() -> None:
    # Arrange
    session = MagicMock()

    # Act
    mark_event_processed(
        session,
        'evt-123',
        event_type='INSERT',
        table_name='contacts',
    )

    # Assert
    assert session.add.call_count == 1
    added = session.add.call_args[0][0]
    assert isinstance(added, ProcessedStreamEvent)
    assert added.event_id == 'evt-123'
    assert added.event_type == 'INSERT'
    assert added.table_name == 'contacts'
