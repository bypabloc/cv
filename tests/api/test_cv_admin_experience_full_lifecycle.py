"""E2E del lifecycle COMPLETO de `experience` via el Lambda cv_admin.

Plantilla canonica (doc 11): CREATE con el payload completo (role/company/
country/companyUrl/start/end/seniority/summary/metricsEstimated/bullets/
skills/niches/priority) -> READ publica via GET /cv experiences (cache
invalidado por tag 'cv') -> READ por niche -> UPDATE (role.en, una
responsibility nueva en posicion 0, achievement[1] eliminado,
skillsTechnical sin la skill nueva, niches -> solo [generic], end -> null
"Presente") -> DELETE -> DELETE idempotente (4404 SLUG_NOT_FOUND exacto).

`skillsTechnical`/`skillsSoft` se assertan por SET + largo: el GET ordena
por `Skill.name` con la collation de PostgreSQL (no portable a `sorted()`
de Python).
"""

from __future__ import annotations

import secrets

import pytest

from ._cv_admin_flows import CvAdminSession
from ._cv_admin_flows import LifecycleSpec
from ._cv_admin_flows import run_entity_lifecycle
from ._cv_admin_flows import synthetic_slug


@pytest.mark.api
def test_cv_admin_experience_full_lifecycle(
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin sintetica contra cv_admin en dev,
    When recorre los 6 pasos del lifecycle de una experience sintetica,
    Then cada paso responde su contrato exacto y el GET publico refleja
    create/update/delete sin tocar slugs reales. [AC-1, AC-3, AC-4, AC-11]
    """
    session = cv_admin_session
    slug = synthetic_slug('exp')
    skill_a, skill_b = session.existing_names('skills', 2)
    soft_skill = session.existing_names('skills', 3)[2]
    new_skill = f'e2e-cvadm-skill-{secrets.token_hex(3)}'
    session.register_vocab('skill', new_skill)

    create = {
        'slug': slug,
        'role': {'es': 'Ingeniero E2E', 'en': 'E2E Engineer'},
        'company': 'E2E Cvadm Corp',
        'country': 'Chile',
        'companyUrl': 'https://example.com/e2e-cvadm',
        'start': '2023-02',
        'end': '2024-08',
        'seniority': 'senior',
        'summary': {
            'es': 'Resumen sintetico es.',
            'en': 'Synthetic summary en.',
        },
        'metricsEstimated': True,
        'responsibilities': {
            'es': ['Resp uno es', 'Resp dos es'],
            'en': ['Resp one en', 'Resp two en'],
        },
        'achievements': {
            'es': ['Logro uno es', 'Logro dos es'],
            'en': ['Ach one en', 'Ach two en'],
        },
        'skillsTechnical': [skill_a, skill_b, new_skill],
        'skillsSoft': [soft_skill],
        'niches': ['generic', 'vibe'],
        'priority': {'generic': 5, 'vibe': 3},
    }
    update = {
        **create,
        'role': {'es': 'Ingeniero E2E', 'en': 'E2E Engineer (updated)'},
        'responsibilities': {
            'es': ['Resp cero es', 'Resp uno es', 'Resp dos es'],
            'en': ['Resp zero en', 'Resp one en', 'Resp two en'],
        },
        'achievements': {
            'es': ['Logro uno es'],
            'en': ['Ach one en'],
        },
        'skillsTechnical': [skill_a, skill_b],
        'niches': ['generic'],
        'priority': {'generic': 5},
        'end': None,
    }

    spec = LifecycleSpec(
        action_suffix='experience',
        get_action='experiences',
        slug=slug,
        create_payload=create,
        update_payload=update,
        niche_in='generic',
        niche_out='fintech',
        create_expect={
            'slug': slug,
            'company': 'E2E Cvadm Corp',
            'country': 'Chile',
            'companyUrl': 'https://example.com/e2e-cvadm',
            'start': '2023-02',
            'end': '2024-08',
            'seniority': 'senior',
            'metricsEstimated': True,
            'role': {'es': 'Ingeniero E2E', 'en': 'E2E Engineer'},
            'summary': {
                'es': 'Resumen sintetico es.',
                'en': 'Synthetic summary en.',
            },
            'responsibilities': {
                'es': ['Resp uno es', 'Resp dos es'],
                'en': ['Resp one en', 'Resp two en'],
            },
            'achievements': {
                'es': ['Logro uno es', 'Logro dos es'],
                'en': ['Ach one en', 'Ach two en'],
            },
            'niches': ['vibe', 'generic'],
            'priority': {'generic': 5, 'vibe': 3},
        },
        create_expect_sets={
            'skillsTechnical': {skill_a, skill_b, new_skill},
            'skillsSoft': {soft_skill},
        },
        update_expect={
            'role': {'es': 'Ingeniero E2E', 'en': 'E2E Engineer (updated)'},
            'responsibilities': {
                'es': ['Resp cero es', 'Resp uno es', 'Resp dos es'],
                'en': ['Resp zero en', 'Resp one en', 'Resp two en'],
            },
            'achievements': {
                'es': ['Logro uno es'],
                'en': ['Ach one en'],
            },
            'niches': ['generic'],
            'priority': {'generic': 5},
            'start': '2023-02',
        },
        update_expect_sets={
            'skillsTechnical': {skill_a, skill_b},
            'skillsSoft': {soft_skill},
        },
        update_absent=('end',),
        update_niche_out='vibe',
    )

    run_entity_lifecycle(session, spec)
