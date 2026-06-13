"""E2E del lifecycle COMPLETO de `certificate` via el Lambda cv_admin.

Plantilla canonica (doc 11): CREATE (title/issuer/date/url/niches
[generic, fintech]/priority) -> READ publica via GET /cv certificates ->
READ por niche -> UPDATE (title; niches -> solo [generic]) -> DELETE ->
DELETE idempotente (4404 SLUG_NOT_FOUND exacto).

El GET certificates serializa `date` como ISO completo (`YYYY-MM-DD`) y
ordena `niches` por display_order (fintech antes que generic).
"""

from __future__ import annotations

import pytest

from ._cv_admin_flows import CvAdminSession
from ._cv_admin_flows import LifecycleSpec
from ._cv_admin_flows import run_entity_lifecycle
from ._cv_admin_flows import synthetic_slug


@pytest.mark.api
def test_cv_admin_certificate_full_lifecycle(
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin sintetica contra las operations admin del cv en dev,
    When recorre los 6 pasos del lifecycle de un certificate sintetico,
    Then cada paso responde su contrato exacto (incl. el cambio de niches
    en el update) y el GET publico refleja create/update/delete.
    [AC-1, AC-3, AC-4, AC-11]
    """
    slug = synthetic_slug('cert')
    create = {
        'slug': slug,
        'title': 'E2E Cvadm Certification',
        'issuer': 'E2E Cvadm Issuer',
        'date': '2024-06-15',
        'url': 'https://example.com/e2e-cvadm-cert',
        'niches': ['generic', 'fintech'],
        'priority': {'generic': 1, 'fintech': 2},
    }
    update = {
        **create,
        'title': 'E2E Cvadm Certification (renewed)',
        'niches': ['generic'],
        'priority': {'generic': 1},
    }

    spec = LifecycleSpec(
        action_suffix='certificate',
        get_action='certificates',
        slug=slug,
        create_payload=create,
        update_payload=update,
        niche_in='fintech',
        niche_out='vibe',
        create_expect={
            'slug': slug,
            'title': 'E2E Cvadm Certification',
            'issuer': 'E2E Cvadm Issuer',
            'date': '2024-06-15',
            'url': 'https://example.com/e2e-cvadm-cert',
            'niches': ['fintech', 'generic'],
        },
        update_expect={
            'title': 'E2E Cvadm Certification (renewed)',
            'issuer': 'E2E Cvadm Issuer',
            'date': '2024-06-15',
            'niches': ['generic'],
        },
        update_niche_out='fintech',
    )

    run_entity_lifecycle(cv_admin_session, spec)
