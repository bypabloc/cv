"""shared.db.repositories.cv_write.reorder_niche_priorities.

Given 3 entity_ids ordenados para un niche,
When se invoca reorder_niche_priorities,
Then borra las filas previas de esos ids en ese niche y los inserta con
prioridades descendentes 30, 20, 10 (paso 10, primero = mas prominente).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.cv_write import reorder_niche_priorities

pytestmark = pytest.mark.unit


def test_cv_write_reorder_assigns_descending_priorities() -> None:
    # Arrange
    session = MagicMock()
    ordered = ['e-1', 'e-2', 'e-3']

    # Act
    reorder_niche_priorities(session, 'experience', 'n-generic', ordered)

    # Assert: 1 delete + 3 inserts
    assert session.execute.call_count == 4
    inserts = [c[0][0] for c in session.execute.call_args_list[1:]]
    priorities = [
        stmt.compile().params['priority'] for stmt in inserts
    ]
    entity_ids = [
        stmt.compile().params['entity_id'] for stmt in inserts
    ]
    assert priorities == [30, 20, 10]
    assert entity_ids == ['e-1', 'e-2', 'e-3']
