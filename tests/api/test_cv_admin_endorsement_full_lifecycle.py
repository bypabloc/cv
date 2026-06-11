"""E2E del lifecycle COMPLETO de `endorsement` via el Lambda cv_admin.

Plantilla canonica (doc 11): CREATE (name/role/company/linkedin/
relation{es,en}/niches/priority) -> READ publica via GET /cv
`references` (la seccion publica de los endorsements) -> READ por niche
-> UPDATE (relation.en; company -> null) -> DELETE -> DELETE idempotente
(4404 SLUG_NOT_FOUND exacto).
"""

from __future__ import annotations

import pytest

from ._cv_admin_flows import CvAdminSession
from ._cv_admin_flows import LifecycleSpec
from ._cv_admin_flows import run_entity_lifecycle
from ._cv_admin_flows import synthetic_slug


@pytest.mark.api
def test_cv_admin_endorsement_full_lifecycle(
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin sintetica contra las operations admin del cv en dev,
    When recorre los 6 pasos del lifecycle de un endorsement sintetico,
    Then cada paso responde su contrato exacto (incl. company -> null en
    el update) y GET /cv references refleja create/update/delete.
    [AC-1, AC-3, AC-4, AC-11]
    """
    slug = synthetic_slug('endo')
    create = {
        'slug': slug,
        'name': 'E2E Cvadm Person',
        'role': 'QA Lead',
        'company': 'E2E Cvadm Corp',
        'linkedin': 'https://linkedin.com/in/e2e-cvadm',
        'relation': {
            'es': 'Colega sintetico es.',
            'en': 'Synthetic peer en.',
        },
        'niches': ['generic'],
        'priority': {'generic': 1},
    }
    update = {
        **create,
        'relation': {
            'es': 'Colega sintetico es.',
            'en': 'Synthetic peer en (updated).',
        },
        'company': None,
    }

    spec = LifecycleSpec(
        action_suffix='endorsement',
        get_action='references',
        slug=slug,
        create_payload=create,
        update_payload=update,
        niche_in='generic',
        niche_out='fintech',
        create_expect={
            'slug': slug,
            'name': 'E2E Cvadm Person',
            'role': 'QA Lead',
            'company': 'E2E Cvadm Corp',
            'linkedin': 'https://linkedin.com/in/e2e-cvadm',
            'relation': {
                'es': 'Colega sintetico es.',
                'en': 'Synthetic peer en.',
            },
            'niches': ['generic'],
        },
        update_expect={
            'relation': {
                'es': 'Colega sintetico es.',
                'en': 'Synthetic peer en (updated).',
            },
            'name': 'E2E Cvadm Person',
            'niches': ['generic'],
        },
        update_absent=('company',),
    )

    run_entity_lifecycle(cv_admin_session, spec)
