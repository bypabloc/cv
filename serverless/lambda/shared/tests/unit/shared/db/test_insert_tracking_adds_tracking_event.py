"""shared.db.repository.insert_tracking.

Given una Session y un payload de tracking event,
When se invoca insert_tracking,
Then agrega a la Session una fila TrackingEvent con los campos del
     payload.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from shared.db.models import TrackingEvent
from shared.db.repository import insert_tracking

pytestmark = pytest.mark.unit


def test_insert_tracking_adds_tracking_event() -> None:
    # Arrange
    session = MagicMock()
    payload = {
        'session_id': 's-1',
        'page_id': 'p-1',
        'page_path': '/projects',
    }

    # Act
    insert_tracking(session, payload)

    # Assert
    assert session.add.call_count == 1
    added = session.add.call_args[0][0]
    assert isinstance(added, TrackingEvent)
    assert added.session_id == 's-1'
    assert added.page_id == 'p-1'
    assert added.page_path == '/projects'
