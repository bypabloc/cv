"""shared.db.repositories.cv_write_entities.upsert_experience.

Given un payload de experiencia con skills y SIN skill_ids precomputados
(path del cv_admin),
When se invoca upsert_experience,
Then upsertea los skills referenciados al catalogo on-the-fly (mismo
criterio que el seed) y devuelve el id de la experiencia.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.cv_write_entities import upsert_experience

pytestmark = pytest.mark.unit


def test_cv_write_entities_upsert_experience_ensures_skills_on_the_fly() -> None:
    # Arrange: scalar_one devuelve ids para vocab/entidad/bullets;
    # scalars().all() devuelve [] (sin bullets previos).
    session = MagicMock()
    session.execute.return_value.scalar_one.return_value = 'row-id'
    session.execute.return_value.scalars.return_value.all.return_value = []
    data = {
        'slug': 'e2e-exp',
        'company': 'Acme',
        'country': 'Chile',
        'start': '2024-01',
        'seniority': 'senior',
        'role': {'es': 'Dev', 'en': 'Dev'},
        'skillsTechnical': ['Python'],
        'skillsSoft': ['Liderazgo'],
        'niches': ['generic'],
        'priority': {'generic': 5},
    }

    # Act
    exp_id = upsert_experience(session, data, {'generic': 'n-gen'})

    # Assert: devuelve el id y ejecuto los upserts del vocabulario
    # (2 skills) ademas de la entidad — minimo 3 statements con
    # scalar_one consumido.
    assert exp_id == 'row-id'
    scalar_one_calls = [
        c
        for c in session.execute.call_args_list
        if 'cv_skills' in str(c[0][0]) or 'cv_experiences' in str(c[0][0])
    ]
    assert len(scalar_one_calls) == 3
