"""E2E del lifecycle COMPLETO de `education` via el Lambda cv_admin.

Plantilla canonica (doc 11): CREATE (institution/degree/description/
start/end/url/niches) -> READ publica via GET /cv education -> READ por
niche -> UPDATE (degree.es, end -> null, url) -> DELETE -> DELETE
idempotente (4404 SLUG_NOT_FOUND exacto).

El GET education serializa `start`/`end` como ANO (`%Y`): un create con
`start='2018-03'` vuelve como `'2018'`.
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
def test_cv_admin_education_full_lifecycle(
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin sintetica contra cv_admin en dev,
    When recorre los 6 pasos del lifecycle de una education sintetica,
    Then cada paso responde su contrato exacto y el GET publico refleja
    create/update/delete. [AC-1, AC-3, AC-4, AC-11]
    """
    slug = synthetic_slug('edu')
    create = {
        'slug': slug,
        'institution': 'E2E Cvadm Institute',
        'degree': {'es': 'Grado sintetico', 'en': 'Synthetic degree'},
        'description': {
            'es': 'Descripcion educacion es.',
            'en': 'Education description en.',
        },
        'start': '2018-03',
        'end': '2022-12',
        'url': 'https://example.com/e2e-cvadm-edu',
        'niches': ['generic'],
        'priority': {'generic': 2},
    }
    update = {
        **create,
        'degree': {
            'es': 'Grado sintetico (actualizado)',
            'en': 'Synthetic degree',
        },
        'end': None,
        'url': 'https://example.com/e2e-cvadm-edu-v2',
    }

    spec = LifecycleSpec(
        action_suffix='education',
        get_action='education',
        slug=slug,
        create_payload=create,
        update_payload=update,
        niche_in='generic',
        niche_out='fintech',
        create_expect={
            'slug': slug,
            'institution': 'E2E Cvadm Institute',
            'degree': {'es': 'Grado sintetico', 'en': 'Synthetic degree'},
            'description': {
                'es': 'Descripcion educacion es.',
                'en': 'Education description en.',
            },
            'start': '2018',
            'end': '2022',
            'url': 'https://example.com/e2e-cvadm-edu',
            'niches': ['generic'],
        },
        update_expect={
            'degree': {
                'es': 'Grado sintetico (actualizado)',
                'en': 'Synthetic degree',
            },
            'url': 'https://example.com/e2e-cvadm-edu-v2',
            'start': '2018',
            'niches': ['generic'],
        },
        update_absent=('end',),
    )

    run_entity_lifecycle(cv_admin_session, spec)
