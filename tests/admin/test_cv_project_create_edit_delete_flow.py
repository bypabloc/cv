"""Flujo COMPLETO (10 pasos) de un proyecto en /cv/projects.

Doc 12 (`test_cv_project_create_edit_delete_flow`): alta con TODOS los
campos del form de proyecto (name/url/repo, links {label,url}, status y
projectType via Select, toggles, summary/description BiLang, metrics
key/value ORDENADAS con reorden, stack con tech-tags del catalogo + uno
nuevo, case study detallado problem/process/result es/en), persistencia
tras reload, hidratacion exacta, mutaciones (metric nueva al inicio, link
eliminado, status -> inactive, caseStudyResult.en), espejo API (metrics en
orden, stack sin duplicados, case study completo), delete y teardown.

Nota: el doc 12 nombra el case study "caseStudy {problem,process,result}";
en el contrato real ese bloque es `caseStudyDetailed` y el form lo expone
como los pares BiLang `caseStudyProblem`/`caseStudyProcess`/
`caseStudyResult` (mas el resumen `caseStudy`, que aqui no se usa).
"""

from __future__ import annotations

import secrets

from api._cv_admin_flows import CvAdminSession
from api._cv_admin_flows import find_one

from ._cv_ui import ACTION_TIMEOUT
from ._cv_ui import TAG_UI
from ._cv_ui import add_pair
from ._cv_ui import add_tag_from_suggestion
from ._cv_ui import add_tag_new
from ._cv_ui import bilang_values
from ._cv_ui import card
from ._cv_ui import cards_count
from ._cv_ui import close_dialog
from ._cv_ui import delete_entity
from ._cv_ui import dom_slugs
from ._cv_ui import field_value
from ._cv_ui import fill_bilang
from ._cv_ui import fill_field
from ._cv_ui import goto_cv_overview
from ._cv_ui import move_pair_up
from ._cv_ui import niche_checked
from ._cv_ui import niche_priority_value
from ._cv_ui import open_edit_entity
from ._cv_ui import open_new_entity
from ._cv_ui import open_section
from ._cv_ui import pair_values
from ._cv_ui import reload_section
from ._cv_ui import remove_pair
from ._cv_ui import save_entity
from ._cv_ui import select_option
from ._cv_ui import select_value
from ._cv_ui import set_niche
from ._cv_ui import set_switch
from ._cv_ui import switch_checked
from ._cv_ui import tag_values
from ._cv_ui import ui_slug
from .conftest import CvAdminPage


_DEMO_URL = 'https://example.com/e2e-cvadm-ui/demo'
_DOCS_URL = 'https://example.com/e2e-cvadm-ui/docs'


def test_cv_project_create_edit_delete_flow(
    cv_page: CvAdminPage,
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin real en /cv/projects,
    When crea un proyecto sintetico con TODOS los campos, lo recarga, lo
        reabre, lo muta y lo elimina,
    Then la hidratacion es exacta campo a campo (incl. orden de metrics y
        stack), el GET /cv refleja metrics en orden, stack sin duplicados
        y el case study completo, y la lista termina igual al inicio con
        cero errores de consola.
    """
    # Arrange.
    page = cv_page.page
    session = cv_admin_session
    slug = ui_slug('proj')
    session.register('project', slug)
    tag_a, tag_b = session.existing_names('techTags', 2)
    new_tag = f'{TAG_UI}-tag-{secrets.token_hex(3)}'
    session.register_vocab('tech_tag', new_tag)

    # 1. Navegar a la seccion + conteo inicial.
    goto_cv_overview(page)
    open_section(page, 'projects')
    initial = cards_count(page)

    # 2. Alta: el form abre vacio.
    open_new_entity(page)
    assert field_value(page, 'cv-field-slug') == ''
    assert field_value(page, 'cv-field-name') == ''

    # 3. Llenar TODOS los campos.
    fill_field(page, 'cv-field-slug', slug)
    fill_field(page, 'cv-field-name', 'E2E Cvadm UI Project')
    fill_bilang(page, 'summary', 'Summary proyecto es.', 'Project summary en.')
    fill_bilang(page, 'description', 'Descripcion es.', 'Description en.')
    fill_field(page, 'cv-field-url', 'https://example.com/e2e-cvadm-ui-proj')
    fill_field(page, 'cv-field-repo', 'https://github.com/bypabloc/e2e-cvadm')
    # Links: 2 pares {label, url}.
    add_pair(page, 'cv-link', 'demo', _DEMO_URL)
    add_pair(page, 'cv-link', 'docs', _DOCS_URL)
    select_option(page, 'cv-field-status', 'active')
    select_option(page, 'cv-field-projectType', 'web')
    set_switch(page, 'cv-field-isConfidential', on=False)
    set_switch(page, 'cv-field-metricsEstimated', on=True)
    # Stack: 2 tech-tags reales del catalogo + 1 nuevo.
    add_tag_from_suggestion(page, 'stack', tag_a)
    add_tag_from_suggestion(page, 'stack', tag_b)
    add_tag_new(page, 'stack', new_tag)
    assert tag_values(page, 'stack') == [tag_a, tag_b, new_tag]
    # Case study detallado: problem/process/result es y en (6 textareas).
    fill_bilang(page, 'caseStudyProblem', 'Problema es.', 'Problem en.')
    fill_bilang(page, 'caseStudyProcess', 'Proceso es.', 'Process en.')
    fill_bilang(page, 'caseStudyResult', 'Resultado es.', 'Result en.')
    # Metricas ordenadas: 2 pares + reorder (subir metric[1]).
    add_pair(page, 'cv-metric', 'users-migrated', '1200')
    add_pair(page, 'cv-metric', 'latency-p95', '350ms')
    move_pair_up(page, 'cv-metric', 1)
    assert pair_values(page, 'cv-metric') == [
        ('latency-p95', '350ms'),
        ('users-migrated', '1200'),
    ]
    # Niches: generic con prioridad 4.
    set_niche(page, 'generic', priority=4)

    # 4. Guardar: toast + dialog cierra + card nueva visible.
    save_entity(page, action='upsert-project')
    card(page, slug).wait_for(state='visible', timeout=ACTION_TIMEOUT)
    card_text = card(page, slug).inner_text()
    assert ('E2E Cvadm UI Project' in card_text) is True
    assert ('web · active' in card_text) is True
    assert ('generic' in card_text) is True

    # 5. Reload: persiste.
    reload_section(page)
    assert cards_count(page) == initial + 1
    assert dom_slugs(page).count(slug) == 1

    # 6. Reabrir editar: HIDRATACION EXACTA.
    open_edit_entity(page, slug)
    assert field_value(page, 'cv-field-slug') == slug
    assert page.locator('[data-testid=cv-field-slug]').is_disabled() is True
    assert field_value(page, 'cv-field-name') == 'E2E Cvadm UI Project'
    assert bilang_values(page, 'summary') == (
        'Summary proyecto es.',
        'Project summary en.',
    )
    assert bilang_values(page, 'description') == (
        'Descripcion es.',
        'Description en.',
    )
    assert field_value(page, 'cv-field-url') == (
        'https://example.com/e2e-cvadm-ui-proj'
    )
    assert field_value(page, 'cv-field-repo') == (
        'https://github.com/bypabloc/e2e-cvadm'
    )
    assert pair_values(page, 'cv-link') == [
        ('demo', _DEMO_URL),
        ('docs', _DOCS_URL),
    ]
    assert select_value(page, 'cv-field-status') == 'active'
    assert select_value(page, 'cv-field-projectType') == 'web'
    assert switch_checked(page, 'cv-field-isConfidential') is False
    assert switch_checked(page, 'cv-field-metricsEstimated') is True
    assert tag_values(page, 'stack') == [tag_a, tag_b, new_tag]
    assert bilang_values(page, 'caseStudyProblem') == (
        'Problema es.',
        'Problem en.',
    )
    assert bilang_values(page, 'caseStudyProcess') == (
        'Proceso es.',
        'Process en.',
    )
    assert bilang_values(page, 'caseStudyResult') == (
        'Resultado es.',
        'Result en.',
    )
    assert pair_values(page, 'cv-metric') == [
        ('latency-p95', '350ms'),
        ('users-migrated', '1200'),
    ]
    assert niche_checked(page, 'generic') is True
    assert niche_priority_value(page, 'generic') == '4'

    # 7. Mutar: metric nueva AL INICIO (agregar + subir dos veces), link
    #    eliminado, status -> inactive, caseStudyResult.en.
    add_pair(page, 'cv-metric', 'e2e-new-metric', '7')
    move_pair_up(page, 'cv-metric', 2)
    move_pair_up(page, 'cv-metric', 1)
    assert pair_values(page, 'cv-metric') == [
        ('e2e-new-metric', '7'),
        ('latency-p95', '350ms'),
        ('users-migrated', '1200'),
    ]
    remove_pair(page, 'cv-link', 0)
    assert pair_values(page, 'cv-link') == [('docs', _DOCS_URL)]
    select_option(page, 'cv-field-status', 'inactive')
    fill_bilang(
        page,
        'caseStudyResult',
        'Resultado es.',
        'Result en (updated).',
    )
    save_entity(page, action='upsert-project')

    # 8. Verificar: reabrir -> mutaciones exactas.
    open_edit_entity(page, slug)
    assert pair_values(page, 'cv-metric') == [
        ('e2e-new-metric', '7'),
        ('latency-p95', '350ms'),
        ('users-migrated', '1200'),
    ]
    assert pair_values(page, 'cv-link') == [('docs', _DOCS_URL)]
    assert select_value(page, 'cv-field-status') == 'inactive'
    assert bilang_values(page, 'caseStudyResult') == (
        'Resultado es.',
        'Result en (updated).',
    )
    close_dialog(page)

    # 8b. Espejo API: metrics en orden, stack sin duplicados, case study
    #     completo.
    entity = find_one(session.cv_get('projects'), slug)
    assert list(entity['metrics'].keys()) == [
        'e2e-new-metric',
        'latency-p95',
        'users-migrated',
    ]
    assert entity['metrics'] == {
        'e2e-new-metric': '7',
        'latency-p95': '350ms',
        'users-migrated': '1200',
    }
    assert entity['stack'] == [tag_a, tag_b, new_tag]
    assert len(entity['stack']) == len(set(entity['stack']))
    assert entity['links'] == [{'label': 'docs', 'url': _DOCS_URL}]
    assert entity['status'] == 'inactive'
    assert entity['caseStudyDetailed'] == {
        'problem': {'es': 'Problema es.', 'en': 'Problem en.'},
        'process': {'es': 'Proceso es.', 'en': 'Process en.'},
        'result': {'es': 'Resultado es.', 'en': 'Result en (updated).'},
    }
    assert entity['niches'] == ['generic']

    # 9. Eliminar + reload ausente.
    delete_entity(page, slug, action='delete-project')
    reload_section(page)
    assert cards_count(page) == initial
    assert dom_slugs(page).count(slug) == 0

    # 10. Teardown idempotente via API + cero errores de consola.
    session.post('delete-project', {'slug': slug}, retries=2, delay=1.0)
    assert cv_page.console_errors == []
