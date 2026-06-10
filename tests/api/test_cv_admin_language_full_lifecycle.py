"""E2E del lifecycle COMPLETO de `language` via el Lambda cv_admin.

Plantilla canonica (doc 11): CREATE (name{es,en}/level{es,en}/niches/
priority) -> READ publica via GET /cv languages -> READ por niche ->
UPDATE (level.es) -> DELETE -> DELETE idempotente (4404 SLUG_NOT_FOUND
exacto).
"""

from __future__ import annotations

import pytest

from ._cv_admin_flows import (
    CvAdminSession,
    LifecycleSpec,
    run_entity_lifecycle,
    synthetic_slug,
)


@pytest.mark.api
def test_cv_admin_language_full_lifecycle(
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin sintetica contra cv_admin en dev,
    When recorre los 6 pasos del lifecycle de un language sintetico,
    Then cada paso responde su contrato exacto y el GET publico refleja
    create/update/delete. [AC-1, AC-3, AC-4, AC-11]
    """
    slug = synthetic_slug('lang')
    create = {
        'slug': slug,
        'name': {'es': 'Esperanto E2E', 'en': 'E2E Esperanto'},
        'level': {'es': 'Basico', 'en': 'Basic'},
        'niches': ['generic'],
        'priority': {'generic': 1},
    }
    update = {
        **create,
        'level': {'es': 'Intermedio', 'en': 'Basic'},
    }

    spec = LifecycleSpec(
        action_suffix='language',
        get_action='languages',
        slug=slug,
        create_payload=create,
        update_payload=update,
        niche_in='generic',
        niche_out='architect',
        create_expect={
            'slug': slug,
            'name': {'es': 'Esperanto E2E', 'en': 'E2E Esperanto'},
            'level': {'es': 'Basico', 'en': 'Basic'},
            'niches': ['generic'],
        },
        update_expect={
            'name': {'es': 'Esperanto E2E', 'en': 'E2E Esperanto'},
            'level': {'es': 'Intermedio', 'en': 'Basic'},
            'niches': ['generic'],
        },
    )

    run_entity_lifecycle(cv_admin_session, spec)
