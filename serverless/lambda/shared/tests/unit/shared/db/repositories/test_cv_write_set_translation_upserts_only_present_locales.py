"""shared.db.repositories.cv_write.set_translation.

Given un bloque bilingue con SOLO el locale `es` (en ausente),
When se invoca set_translation,
Then ejecuta exactamente UN upsert (la fila es) y ninguno para en;
y con bilang None no ejecuta nada.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.cv_write import set_translation
from sqlalchemy.dialects import postgresql

pytestmark = pytest.mark.unit


def test_cv_write_set_translation_upserts_only_present_locales() -> None:
    # Arrange
    session = MagicMock()

    # Act
    set_translation(session, 'award', 'a-1', 'title', {'es': 'Premio'})
    set_translation(session, 'award', 'a-1', 'title', None)

    # Assert
    assert session.execute.call_count == 1
    stmt = session.execute.call_args[0][0]
    sql = str(stmt.compile(dialect=postgresql.dialect()))
    assert 'INSERT INTO i18n_translations' in sql
    assert 'ON CONFLICT (entity_type, entity_id, field, locale)' in sql
