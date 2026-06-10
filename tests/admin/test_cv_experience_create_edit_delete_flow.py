"""Flujo COMPLETO (10 pasos, sin atajos) de una experiencia en /cv/experiences.

Doc 12 (`test_cv_experience_create_edit_delete_flow`): alta con TODOS los
campos del form (role BiLang, empresa/pais/URL, fechas, seniority,
metricsEstimated, bullets paralelos con reorden y eliminacion, skills del
catalogo + una nueva, niches generic+vibe con prioridad), persistencia
tras reload, HIDRATACION EXACTA al reabrir, mutaciones (role.en, bullet
nuevo al inicio, skill creada eliminada, niche vibe desmarcado), espejo
API por niche, delete con confirmacion y teardown idempotente via API.

Nota de hidratacion: `skillsTechnical`/`skillsSoft` se assertan por SET +
largo — el GET /cv las ordena por `Skill.name` con la collation de
PostgreSQL (no portable a `sorted()` de Python); el form hidrata en ese
mismo orden.
"""

from __future__ import annotations

import secrets

from api._cv_admin_flows import CvAdminSession
from api._cv_admin_flows import find_one
from api._cv_admin_flows import slugs_of

from ._cv_ui import ACTION_TIMEOUT
from ._cv_ui import TAG_UI
from ._cv_ui import add_bilang_item
from ._cv_ui import add_tag_from_suggestion
from ._cv_ui import add_tag_new
from ._cv_ui import bilang_list_values
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
from ._cv_ui import move_bilang_item_up
from ._cv_ui import niche_checked
from ._cv_ui import niche_priority_value
from ._cv_ui import open_edit_entity
from ._cv_ui import open_new_entity
from ._cv_ui import open_section
from ._cv_ui import reload_section
from ._cv_ui import remove_bilang_item
from ._cv_ui import remove_tag
from ._cv_ui import save_entity
from ._cv_ui import select_option
from ._cv_ui import select_value
from ._cv_ui import set_niche
from ._cv_ui import set_switch
from ._cv_ui import switch_checked
from ._cv_ui import tag_values
from ._cv_ui import ui_slug
from ._cv_ui import unset_niche
from .conftest import CvAdminPage


def test_cv_experience_create_edit_delete_flow(
    cv_page: CvAdminPage,
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin real en /cv/experiences,
    When crea una experiencia sintetica llenando TODOS los campos, la
        recarga, la reabre, la muta y la elimina,
    Then cada paso refleja el estado exacto en la UI (hidratacion campo a
        campo, orden de bullets, tags, niches con prioridad) y en el GET
        /cv por niche, terminando con la lista igual al inicio y cero
        errores de consola.
    """
    # Arrange: datos sinteticos + vocabulario real del catalogo.
    page = cv_page.page
    session = cv_admin_session
    slug = ui_slug('exp')
    session.register('experience', slug)
    skill_a, skill_b = session.existing_names('skills', 2)
    soft_skill = session.existing_names('skills', 3)[2]
    new_skill = f'{TAG_UI}-skill-{secrets.token_hex(3)}'
    session.register_vocab('skill', new_skill)

    # 1. Navegar a la seccion + conteo inicial.
    goto_cv_overview(page)
    open_section(page, 'experiences')
    initial = cards_count(page)

    # 2. Alta: el form abre vacio.
    open_new_entity(page)
    assert field_value(page, 'cv-field-slug') == ''
    assert bilang_values(page, 'role') == ('', '')

    # 3. Llenar TODOS los campos.
    fill_field(page, 'cv-field-slug', slug)
    fill_bilang(page, 'role', 'Ingeniero UI E2E', 'UI E2E Engineer')
    fill_field(page, 'cv-field-company', 'E2E Cvadm UI Corp')
    fill_field(page, 'cv-field-country', 'Chile')
    fill_field(page, 'cv-field-companyUrl', 'https://example.com/e2e-cvadm-ui')
    fill_field(page, 'cv-field-start', '2024-01')
    fill_field(page, 'cv-field-end', '2025-06')
    # Formato de fecha aceptado tal cual (YYYY-MM).
    assert field_value(page, 'cv-field-start') == '2024-01'
    assert field_value(page, 'cv-field-end') == '2025-06'
    select_option(page, 'cv-field-seniority', 'senior')
    set_switch(page, 'cv-field-metricsEstimated', on=True)

    # Bullets: 2 responsibilities + 2 achievements.
    add_bilang_item(page, 'responsibilities', 'Resp uno es', 'Resp one en')
    add_bilang_item(page, 'responsibilities', 'Resp dos es', 'Resp two en')
    add_bilang_item(page, 'achievements', 'Logro uno es', 'Ach one en')
    add_bilang_item(page, 'achievements', 'Logro dos es', 'Ach two en')
    # Reordenar: subir achievement[1] a la posicion 0.
    move_bilang_item_up(page, 'achievements', 1)
    assert bilang_list_values(page, 'achievements') == (
        ['Logro dos es', 'Logro uno es'],
        ['Ach two en', 'Ach one en'],
    )
    # Eliminar responsibility[1]: queda 1.
    remove_bilang_item(page, 'responsibilities', 1)
    assert bilang_list_values(page, 'responsibilities') == (
        ['Resp uno es'],
        ['Resp one en'],
    )

    # Skills: 2 sugerencias reales del catalogo + 1 nueva; 1 blanda real.
    add_tag_from_suggestion(page, 'skillsTechnical', skill_a)
    add_tag_from_suggestion(page, 'skillsTechnical', skill_b)
    add_tag_new(page, 'skillsTechnical', new_skill)
    assert tag_values(page, 'skillsTechnical') == [
        skill_a,
        skill_b,
        new_skill,
    ]
    add_tag_from_suggestion(page, 'skillsSoft', soft_skill)
    assert tag_values(page, 'skillsSoft') == [soft_skill]

    # Niches: generic prio 5 + vibe prio 3.
    set_niche(page, 'generic', priority=5)
    set_niche(page, 'vibe', priority=3)

    # 4. Guardar: toast + dialog cierra + card nueva exacta.
    save_entity(page, action='upsert-experience')
    card(page, slug).wait_for(state='visible', timeout=ACTION_TIMEOUT)
    card_text = card(page, slug).inner_text()
    assert ('Ingeniero UI E2E' in card_text) is True
    assert ('E2E Cvadm UI Corp · 2024-01 — 2025-06' in card_text) is True
    assert ('generic' in card_text) is True
    assert ('vibe' in card_text) is True

    # 5. Reload: persiste (conteo == inicial + 1).
    reload_section(page)
    assert cards_count(page) == initial + 1
    assert dom_slugs(page).count(slug) == 1

    # 6. Reabrir editar: HIDRATACION EXACTA de CADA campo.
    open_edit_entity(page, slug)
    assert field_value(page, 'cv-field-slug') == slug
    assert page.locator('[data-testid=cv-field-slug]').is_disabled() is True
    assert bilang_values(page, 'role') == (
        'Ingeniero UI E2E',
        'UI E2E Engineer',
    )
    assert field_value(page, 'cv-field-company') == 'E2E Cvadm UI Corp'
    assert field_value(page, 'cv-field-country') == 'Chile'
    assert field_value(page, 'cv-field-companyUrl') == (
        'https://example.com/e2e-cvadm-ui'
    )
    assert field_value(page, 'cv-field-start') == '2024-01'
    assert field_value(page, 'cv-field-end') == '2025-06'
    assert select_value(page, 'cv-field-seniority') == 'senior'
    assert switch_checked(page, 'cv-field-metricsEstimated') is True
    assert bilang_list_values(page, 'responsibilities') == (
        ['Resp uno es'],
        ['Resp one en'],
    )
    assert bilang_list_values(page, 'achievements') == (
        ['Logro dos es', 'Logro uno es'],
        ['Ach two en', 'Ach one en'],
    )
    hydrated_technical = tag_values(page, 'skillsTechnical')
    assert set(hydrated_technical) == {skill_a, skill_b, new_skill}
    assert len(hydrated_technical) == 3
    assert tag_values(page, 'skillsSoft') == [soft_skill]
    assert niche_checked(page, 'generic') is True
    assert niche_priority_value(page, 'generic') == '5'
    assert niche_checked(page, 'vibe') is True
    assert niche_priority_value(page, 'vibe') == '3'
    assert niche_checked(page, 'fintech') is False

    # 7. Mutar: role.en, responsibility nueva AL INICIO (agregar + subir),
    #    quitar la skill creada, desmarcar vibe.
    fill_bilang(page, 'role', 'Ingeniero UI E2E', 'UI E2E Engineer (updated)')
    add_bilang_item(page, 'responsibilities', 'Resp cero es', 'Resp zero en')
    move_bilang_item_up(page, 'responsibilities', 1)
    assert bilang_list_values(page, 'responsibilities') == (
        ['Resp cero es', 'Resp uno es'],
        ['Resp zero en', 'Resp one en'],
    )
    remove_tag(page, 'skillsTechnical', new_skill)
    unset_niche(page, 'vibe')
    save_entity(page, action='upsert-experience')

    # 8. Verificar: reabrir -> mutaciones exactas.
    open_edit_entity(page, slug)
    assert bilang_values(page, 'role') == (
        'Ingeniero UI E2E',
        'UI E2E Engineer (updated)',
    )
    assert bilang_list_values(page, 'responsibilities') == (
        ['Resp cero es', 'Resp uno es'],
        ['Resp zero en', 'Resp one en'],
    )
    mutated_technical = tag_values(page, 'skillsTechnical')
    assert set(mutated_technical) == {skill_a, skill_b}
    assert len(mutated_technical) == 2
    assert niche_checked(page, 'vibe') is False
    close_dialog(page)

    # 8b. Espejo API: vibe ya NO la incluye; generic SI, con los bullets
    #     en el orden final.
    in_vibe = slugs_of(session.cv_get('experiences', niche='vibe'))
    assert in_vibe.count(slug) == 0
    in_generic = session.cv_get('experiences', niche='generic')
    entity = find_one(in_generic, slug)
    assert entity['role'] == {
        'es': 'Ingeniero UI E2E',
        'en': 'UI E2E Engineer (updated)',
    }
    assert entity['responsibilities'] == {
        'es': ['Resp cero es', 'Resp uno es'],
        'en': ['Resp zero en', 'Resp one en'],
    }
    assert entity['achievements'] == {
        'es': ['Logro dos es', 'Logro uno es'],
        'en': ['Ach two en', 'Ach one en'],
    }
    assert entity['niches'] == ['generic']
    assert set(entity['skillsTechnical']) == {skill_a, skill_b}

    # 9. Eliminar: confirmacion + card desaparece + reload ausente.
    delete_entity(page, slug, action='delete-experience')
    reload_section(page)
    assert cards_count(page) == initial
    assert dom_slugs(page).count(slug) == 0

    # 10. Teardown idempotente via API (ademas del registrado en sesion).
    session.post('delete-experience', {'slug': slug}, retries=2, delay=1.0)
    assert cv_page.console_errors == []
