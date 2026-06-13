"""shared.db.repositories.cv_write.upsert_returning_id.

Given un model con clave natural `slug` y values con campos extra,
When se invoca upsert_returning_id,
Then el statement compilado es INSERT ... ON CONFLICT (slug) DO UPDATE
con SET de los campos no-clave (propagacion de cambios) + RETURNING id,
y la funcion devuelve el id del scalar_one().
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from shared.db.models.taxonomy.catalog import TechTag
from shared.db.repositories.cv_write import upsert_returning_id
from sqlalchemy.dialects import postgresql

pytestmark = pytest.mark.unit


def test_cv_write_upsert_returning_id_propagates_values() -> None:
    # Arrange
    session = MagicMock()
    session.execute.return_value.scalar_one.return_value = 'tt-1'

    # Act
    returned = upsert_returning_id(
        session,
        TechTag,
        'slug',
        {'slug': 'aws-lambda', 'name': 'AWS Lambda'},
    )

    # Assert
    assert returned == 'tt-1'
    assert session.execute.call_count == 1
    stmt = session.execute.call_args[0][0]
    sql = str(stmt.compile(dialect=postgresql.dialect()))
    assert 'ON CONFLICT (slug) DO UPDATE' in sql
    assert 'SET name = excluded.name' in sql
    assert 'RETURNING tax_tech_tags.id' in sql
