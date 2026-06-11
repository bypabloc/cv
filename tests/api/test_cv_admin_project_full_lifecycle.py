"""E2E del lifecycle COMPLETO de `project` via el Lambda cv_admin.

Plantilla canonica (doc 11): CREATE con el payload completo (name/url/
repo/links/status/projectType/isConfidential/metricsEstimated/summary/
description/metrics ordenadas/stack con un tech tag NUEVO/caseStudy/
caseStudyDetailed/niches/priority) -> READ publica via GET /cv projects ->
READ por niche -> UPDATE (metric nueva al inicio, metric[1] eliminada,
stack sin el tag nuevo, caseStudyDetailed.result.en, status -> inactive)
-> DELETE -> DELETE idempotente (4404 SLUG_NOT_FOUND exacto).

El doc 11 nombra "caseStudy {problem,process,result}" — en el contrato
real ese bloque es `caseStudyDetailed`; `caseStudy` es un BiLang simple.
Se cubren AMBOS. El orden de `metrics` (dict por position) se asserta via
la lista exacta de keys.
"""

from __future__ import annotations

import secrets

import pytest

from ._cv_admin_flows import CvAdminSession
from ._cv_admin_flows import LifecycleSpec
from ._cv_admin_flows import run_entity_lifecycle
from ._cv_admin_flows import synthetic_slug


@pytest.mark.api
def test_cv_admin_project_full_lifecycle(
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin sintetica contra las operations admin del cv en dev,
    When recorre los 6 pasos del lifecycle de un project sintetico,
    Then cada paso responde su contrato exacto (incl. orden de stack y
    metrics) y el GET publico refleja create/update/delete.
    [AC-1, AC-3, AC-4, AC-11]
    """
    session = cv_admin_session
    slug = synthetic_slug('proj')
    tag_a, tag_b = session.existing_names('techTags', 2)
    new_tag = f'e2e-cvadm-tag-{secrets.token_hex(3)}'
    session.register_vocab('tech_tag', new_tag)

    links = [
        {'label': 'demo', 'url': 'https://example.com/e2e-cvadm/demo'},
        {'label': 'docs', 'url': 'https://example.com/e2e-cvadm/docs'},
    ]
    case_detailed = {
        'problem': {'es': 'Problema es.', 'en': 'Problem en.'},
        'process': {'es': 'Proceso es.', 'en': 'Process en.'},
        'result': {'es': 'Resultado es.', 'en': 'Result en.'},
    }
    create = {
        'slug': slug,
        'name': 'E2E Cvadm Project',
        'summary': {'es': 'Summary proyecto es.', 'en': 'Project summary en.'},
        'description': {'es': 'Descripcion es.', 'en': 'Description en.'},
        'url': 'https://example.com/e2e-cvadm-project',
        'repo': 'https://github.com/bypabloc/e2e-cvadm',
        'links': links,
        'status': 'active',
        'projectType': 'web',
        'isConfidential': False,
        'metricsEstimated': True,
        'stack': [tag_a, tag_b, new_tag],
        'caseStudy': {'es': 'Caso de estudio es.', 'en': 'Case study en.'},
        'caseStudyDetailed': case_detailed,
        'metrics': {'users-migrated': '1200', 'latency-p95': '350ms'},
        'niches': ['generic'],
        'priority': {'generic': 4},
    }
    updated_detailed = {
        **case_detailed,
        'result': {'es': 'Resultado es.', 'en': 'Result en (updated).'},
    }
    update = {
        **create,
        'metrics': {'e2e-new-metric': '7', 'users-migrated': '1200'},
        'stack': [tag_a, tag_b],
        'caseStudyDetailed': updated_detailed,
        'status': 'inactive',
    }

    spec = LifecycleSpec(
        action_suffix='project',
        get_action='projects',
        slug=slug,
        create_payload=create,
        update_payload=update,
        niche_in='generic',
        niche_out='fintech',
        create_expect={
            'slug': slug,
            'name': 'E2E Cvadm Project',
            'summary': {
                'es': 'Summary proyecto es.',
                'en': 'Project summary en.',
            },
            'description': {
                'es': 'Descripcion es.',
                'en': 'Description en.',
            },
            'url': 'https://example.com/e2e-cvadm-project',
            'repo': 'https://github.com/bypabloc/e2e-cvadm',
            'links': links,
            'status': 'active',
            'projectType': 'web',
            'isConfidential': False,
            'metricsEstimated': True,
            'stack': [tag_a, tag_b, new_tag],
            'caseStudy': {
                'es': 'Caso de estudio es.',
                'en': 'Case study en.',
            },
            'caseStudyDetailed': case_detailed,
            'metrics': {'users-migrated': '1200', 'latency-p95': '350ms'},
            'niches': ['generic'],
            'priority': {'generic': 4},
        },
        create_expect_key_order={
            'metrics': ['users-migrated', 'latency-p95'],
        },
        update_expect={
            'metrics': {'e2e-new-metric': '7', 'users-migrated': '1200'},
            'stack': [tag_a, tag_b],
            'caseStudyDetailed': updated_detailed,
            'status': 'inactive',
            'niches': ['generic'],
        },
        update_expect_key_order={
            'metrics': ['e2e-new-metric', 'users-migrated'],
        },
    )

    run_entity_lifecycle(session, spec)
