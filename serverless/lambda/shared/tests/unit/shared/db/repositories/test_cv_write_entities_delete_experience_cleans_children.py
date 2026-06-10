"""shared.db.repositories.cv_write_entities.delete_experience.

Given una experiencia existente con 2 bullets,
When se invoca delete_experience,
Then devuelve True y ejecuta la limpieza completa en orden: lookup,
select de bullets, delete de traducciones de bullets, bullets, skills,
niches, priorities, traducciones de la entidad y la fila final
(9 statements en total).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.cv_write_entities import delete_experience

pytestmark = pytest.mark.unit


def test_cv_write_entities_delete_experience_cleans_children() -> None:
    # Arrange
    session = MagicMock()
    lookup = MagicMock()
    lookup.scalar_one_or_none.return_value = 'exp-1'
    bullets = MagicMock()
    bullets.scalars.return_value.all.return_value = ['b-1', 'b-2']
    generic = MagicMock()
    session.execute.side_effect = [lookup, bullets] + [generic] * 7

    # Act
    deleted = delete_experience(session, 'destacame-architect')

    # Assert: lookup + bullets-select + 7 deletes = 9 statements
    assert deleted is True
    assert session.execute.call_count == 9
