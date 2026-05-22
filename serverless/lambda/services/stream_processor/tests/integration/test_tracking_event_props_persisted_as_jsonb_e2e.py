"""E2E — `event_props` de un tracking record persistido como JSONB.

Given un Stream record INSERT de `tracking` cuyo `event_props` es un
  dict libre con valores anidados (numeros, strings, listas),
When `lambda_handler` procesa el batch end-to-end,
Then `event_props` se persiste en la columna JSONB y al releerlo desde
  el ORM vuelve a ser el mismo dict Python (roundtrip exacto).
"""

from __future__ import annotations

import pytest
from shared.db.models import TrackingEvent
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from tests.integration._fixtures.events import stream_event, tracking_record
from tests.integration._fixtures.runner import invoke_handler

pytestmark = pytest.mark.integration


def test_tracking_event_props_persisted_as_jsonb_e2e(
    sqlite_db: Engine,
) -> None:
    # Arrange — event_props con tipos heterogeneos y anidamiento.
    props = {
        'scroll_depth': 75,
        'cta_label': 'Contactar',
        'tags': ['hero', 'fold'],
        'meta': {'ab_variant': 'b', 'visible_ms': 1200},
    }
    event = stream_event(
        tracking_record('props-evt-1', event_props=props),
    )

    # Act
    result = invoke_handler(event, sqlite_db)

    # Assert
    assert result == {'batchItemFailures': []}

    session = Session(sqlite_db)
    stored = session.query(TrackingEvent).one()
    assert stored.event_props == {
        'scroll_depth': 75,
        'cta_label': 'Contactar',
        'tags': ['hero', 'fold'],
        'meta': {'ab_variant': 'b', 'visible_ms': 1200},
    }
    session.close()
