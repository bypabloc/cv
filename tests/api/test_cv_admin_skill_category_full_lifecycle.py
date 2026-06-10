"""E2E del lifecycle COMPLETO de `skill_category` via el Lambda cv_admin.

Plantilla canonica (doc 11): CREATE (kind technical/name{es,en}/skills [3
ordenadas, 1 NUEVA]/niches/priority) -> READ publica via GET /cv `skills`
(la seccion de categorias) -> READ por niche -> UPDATE (la skill nueva
movida de posicion 2 -> 0, una skill eliminada, name.en) -> DELETE ->
DELETE idempotente (4404 SLUG_NOT_FOUND exacto).

Las `skills` de la categoria se assertan como LISTA exacta: el GET las
ordena por `position` (el orden del payload), a diferencia de las skills
de experience (ordenadas por nombre).
"""

from __future__ import annotations

import secrets

import pytest

from ._cv_admin_flows import CvAdminSession
from ._cv_admin_flows import LifecycleSpec
from ._cv_admin_flows import run_entity_lifecycle
from ._cv_admin_flows import synthetic_slug


@pytest.mark.api
def test_cv_admin_skill_category_full_lifecycle(
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin sintetica contra cv_admin en dev,
    When recorre los 6 pasos del lifecycle de una skill_category sintetica,
    Then cada paso responde su contrato exacto (incl. el orden posicional
    de las skills tras mover la nueva a la posicion 0) y el GET publico
    refleja create/update/delete. [AC-1, AC-3, AC-4, AC-11]
    """
    session = cv_admin_session
    slug = synthetic_slug('skillcat')
    skill_a, skill_b = session.existing_names('skills', 2)
    new_skill = f'e2e-cvadm-catskill-{secrets.token_hex(3)}'
    session.register_vocab('skill', new_skill)

    create = {
        'slug': slug,
        'kind': 'technical',
        'name': {'es': 'Categoria E2E', 'en': 'E2E Category'},
        'skills': [skill_a, skill_b, new_skill],
        'niches': ['generic'],
        'priority': {'generic': 1},
    }
    update = {
        **create,
        'name': {'es': 'Categoria E2E', 'en': 'E2E Category (updated)'},
        'skills': [new_skill, skill_a],
    }

    spec = LifecycleSpec(
        action_suffix='skill-category',
        get_action='skills',
        slug=slug,
        create_payload=create,
        update_payload=update,
        niche_in='generic',
        niche_out='fintech',
        create_expect={
            'slug': slug,
            'kind': 'technical',
            'name': {'es': 'Categoria E2E', 'en': 'E2E Category'},
            'skills': [skill_a, skill_b, new_skill],
            'niches': ['generic'],
        },
        update_expect={
            'kind': 'technical',
            'name': {'es': 'Categoria E2E', 'en': 'E2E Category (updated)'},
            'skills': [new_skill, skill_a],
            'niches': ['generic'],
        },
    )

    run_entity_lifecycle(session, spec)
