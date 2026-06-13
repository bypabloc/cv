"""shared.db.repositories.cv_write_entities.upsert_skill_category.

Given un payload de skill category con niches y prioridad por niche,
When se invoca upsert_skill_category,
Then persiste TAMBIEN el mapa de prioridades via set_niche_priorities
(entity_type 'skill_category') — regresion del editor: sin esto, cada
save desde el admin reseteaba la prioridad del niche a 1.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import shared.db.repositories.cv_write_entities as cv_write_entities

pytestmark = pytest.mark.unit


def test_cv_write_entities_upsert_skill_category_sets_priorities(
    monkeypatch,
) -> None:
    # Arrange: session fake (ids de vocab/entidad) + spy de priorities.
    session = MagicMock()
    session.execute.return_value.scalar_one.return_value = 'cat-id'
    priorities_spy = MagicMock()
    monkeypatch.setattr(
        cv_write_entities, 'set_niche_priorities', priorities_spy,
    )
    niche_ids = {'generic': 'n-gen'}
    data = {
        'slug': 'e2e-cat',
        'kind': 'technical',
        'name': {'es': 'Backend', 'en': 'Backend'},
        'skills': [],
        'niches': ['generic'],
        'priority': {'generic': 2},
    }

    # Act
    cat_id = cv_write_entities.upsert_skill_category(
        session, data, niche_ids
    )

    # Assert: devuelve el id y persistio el mapa de prioridades con el
    # entity_type correcto.
    assert cat_id == 'cat-id'
    priorities_spy.assert_called_once_with(
        session, 'skill_category', 'cat-id', {'generic': 2}, niche_ids
    )
