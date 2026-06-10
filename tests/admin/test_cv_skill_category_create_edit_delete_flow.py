"""Flujo completo (10 pasos) de una skill category en /cv/skills.

Doc 12 (tabla de secciones simples): name es/en, kind Select, skills
tag-input ORDENADO (3 skills: 2 reales del catalogo + 1 nueva, con reorder
interno via tag-chip-up/down), niches+priority. El GET /cv `skills`
preserva el orden por `position` (el del payload), por eso la hidratacion
de los chips se asserta como LISTA exacta. Mutacion: name.en + bajar la
primera skill una posicion.
"""

from __future__ import annotations

import secrets

from api._cv_admin_flows import CvAdminSession
from api._cv_admin_flows import find_one

from ._cv_ui import ACTION_TIMEOUT
from ._cv_ui import TAG_UI
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
from ._cv_ui import move_tag_down
from ._cv_ui import move_tag_up
from ._cv_ui import niche_checked
from ._cv_ui import niche_priority_value
from ._cv_ui import open_edit_entity
from ._cv_ui import open_new_entity
from ._cv_ui import open_section
from ._cv_ui import reload_section
from ._cv_ui import save_entity
from ._cv_ui import select_option
from ._cv_ui import select_value
from ._cv_ui import set_niche
from ._cv_ui import tag_values
from ._cv_ui import ui_slug
from .conftest import CvAdminPage


def test_cv_skill_category_create_edit_delete_flow(
    cv_page: CvAdminPage,
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin real en /cv/skills,
    When crea una categoria sintetica (3 skills ordenadas con reorder
        interno), la reabre, la muta (name.en + primera skill abajo) y la
        elimina,
    Then la hidratacion preserva el ORDEN exacto de las skills, el GET /cv
        skills refleja la lista final por position y la lista termina
        igual al inicio sin errores de consola.
    """
    # Arrange.
    page = cv_page.page
    session = cv_admin_session
    slug = ui_slug('skillcat')
    session.register('skill-category', slug)
    skill_a, skill_b = session.existing_names('skills', 2)
    new_skill = f'{TAG_UI}-skill-{secrets.token_hex(3)}'
    session.register_vocab('skill', new_skill)

    # 1. Navegar a la seccion + conteo inicial.
    goto_cv_overview(page)
    open_section(page, 'skills')
    initial = cards_count(page)

    # 2. Alta: el form abre vacio.
    open_new_entity(page)
    assert field_value(page, 'cv-field-slug') == ''

    # 3. Llenar todos los campos: name BiLang + kind + skills + niches.
    fill_field(page, 'cv-field-slug', slug)
    fill_bilang(page, 'name', 'Categoria UI es', 'UI category en')
    select_option(page, 'cv-field-kind', 'technical')
    add_tag_from_suggestion(page, 'skills', skill_a)
    add_tag_from_suggestion(page, 'skills', skill_b)
    add_tag_new(page, 'skills', new_skill)
    assert tag_values(page, 'skills') == [skill_a, skill_b, new_skill]
    # Reorder interno: subir la skill nueva una posicion.
    move_tag_up(page, 'skills', new_skill)
    assert tag_values(page, 'skills') == [skill_a, new_skill, skill_b]
    set_niche(page, 'generic', priority=2)

    # 4. Guardar.
    save_entity(page, action='upsert-skill-category')
    card(page, slug).wait_for(state='visible', timeout=ACTION_TIMEOUT)

    # 5. Reload: persiste.
    reload_section(page)
    assert cards_count(page) == initial + 1
    assert dom_slugs(page).count(slug) == 1

    # 6. Reabrir editar: hidratacion exacta (orden de skills incluido).
    open_edit_entity(page, slug)
    assert field_value(page, 'cv-field-slug') == slug
    assert page.locator('[data-testid=cv-field-slug]').is_disabled() is True
    assert bilang_values(page, 'name') == ('Categoria UI es', 'UI category en')
    assert select_value(page, 'cv-field-kind') == 'technical'
    assert tag_values(page, 'skills') == [skill_a, new_skill, skill_b]
    assert niche_checked(page, 'generic') is True
    assert niche_priority_value(page, 'generic') == '2'

    # 7. Mutar: name.en + bajar la primera skill una posicion.
    fill_bilang(page, 'name', 'Categoria UI es', 'UI category en (updated)')
    move_tag_down(page, 'skills', skill_a)
    assert tag_values(page, 'skills') == [new_skill, skill_a, skill_b]
    save_entity(page, action='upsert-skill-category')

    # 8. Verificar: reabrir -> mutaciones exactas.
    open_edit_entity(page, slug)
    assert bilang_values(page, 'name') == (
        'Categoria UI es',
        'UI category en (updated)',
    )
    assert tag_values(page, 'skills') == [new_skill, skill_a, skill_b]
    close_dialog(page)

    # 8b. Espejo API: lista exacta por position.
    entity = find_one(session.cv_get('skills'), slug)
    assert entity['name'] == {
        'es': 'Categoria UI es',
        'en': 'UI category en (updated)',
    }
    assert entity['kind'] == 'technical'
    assert entity['skills'] == [new_skill, skill_a, skill_b]
    assert entity['niches'] == ['generic']

    # 9. Eliminar + reload ausente.
    delete_entity(page, slug, action='delete-skill-category')
    reload_section(page)
    assert cards_count(page) == initial
    assert dom_slugs(page).count(slug) == 0

    # 10. Cero errores de consola.
    assert cv_page.console_errors == []
