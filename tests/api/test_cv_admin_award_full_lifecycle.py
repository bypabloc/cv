"""E2E del lifecycle COMPLETO de `award` via el Lambda cv_admin.

Plantilla canonica (doc 11): CREATE (issuer/date/url/title{es,en}/
motivation{es,en}/niches/priority) -> READ publica via GET /cv awards ->
READ por niche -> UPDATE (motivation.en; url -> null) -> DELETE -> DELETE
idempotente (4404 SLUG_NOT_FOUND exacto).

El GET awards serializa `date` como `YYYY-MM` y omite `url` cuando es
null (_drop_nones).
"""

from __future__ import annotations

import pytest

from ._cv_admin_flows import CvAdminSession
from ._cv_admin_flows import LifecycleSpec
from ._cv_admin_flows import run_entity_lifecycle
from ._cv_admin_flows import synthetic_slug


@pytest.mark.api
def test_cv_admin_award_full_lifecycle(
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin sintetica contra cv_admin en dev,
    When recorre los 6 pasos del lifecycle de un award sintetico,
    Then cada paso responde su contrato exacto (incl. url -> null en el
    update) y el GET publico refleja create/update/delete.
    [AC-1, AC-3, AC-4, AC-11]
    """
    slug = synthetic_slug('award')
    create = {
        'slug': slug,
        'issuer': 'E2E Cvadm Foundation',
        'date': '2023-11',
        'url': 'https://example.com/e2e-cvadm-award',
        'title': {'es': 'Premio sintetico', 'en': 'Synthetic award'},
        'motivation': {
            'es': 'Motivacion sintetica es.',
            'en': 'Synthetic motivation en.',
        },
        'niches': ['generic'],
        'priority': {'generic': 1},
    }
    update = {
        **create,
        'motivation': {
            'es': 'Motivacion sintetica es.',
            'en': 'Synthetic motivation en (updated).',
        },
        'url': None,
    }

    spec = LifecycleSpec(
        action_suffix='award',
        get_action='awards',
        slug=slug,
        create_payload=create,
        update_payload=update,
        niche_in='generic',
        niche_out='leader',
        create_expect={
            'slug': slug,
            'issuer': 'E2E Cvadm Foundation',
            'date': '2023-11',
            'url': 'https://example.com/e2e-cvadm-award',
            'title': {'es': 'Premio sintetico', 'en': 'Synthetic award'},
            'motivation': {
                'es': 'Motivacion sintetica es.',
                'en': 'Synthetic motivation en.',
            },
            'niches': ['generic'],
        },
        update_expect={
            'motivation': {
                'es': 'Motivacion sintetica es.',
                'en': 'Synthetic motivation en (updated).',
            },
            'date': '2023-11',
            'niches': ['generic'],
        },
        update_absent=('url',),
    )

    run_entity_lifecycle(cv_admin_session, spec)
