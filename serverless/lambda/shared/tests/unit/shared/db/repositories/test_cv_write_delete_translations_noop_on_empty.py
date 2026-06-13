"""shared.db.repositories.cv_write.delete_translations.

Given una lista vacia de entity_ids,
When se invoca delete_translations,
Then NO ejecuta ningun statement (no-op);
y con ids presentes ejecuta UN delete con IN sobre i18n_translations.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.cv_write import delete_translations
from sqlalchemy.dialects import postgresql

pytestmark = pytest.mark.unit


def test_cv_write_delete_translations_noop_on_empty() -> None:
    # Arrange
    session = MagicMock()

    # Act
    delete_translations(session, 'experience_bullet', [])
    assert session.execute.call_count == 0
    delete_translations(session, 'experience_bullet', ['b-1', 'b-2'])

    # Assert
    assert session.execute.call_count == 1
    stmt = session.execute.call_args[0][0]
    sql = str(stmt.compile(dialect=postgresql.dialect()))
    assert 'DELETE FROM i18n_translations' in sql
    assert 'entity_id IN' in sql
