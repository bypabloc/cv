"""Validacion Zod del form de experiencia (BiLang + fechas) en el dialog.

Doc 12 (`test_cv_bilang_validation_ui`): submit con todo vacio -> el
FormMessage del primer campo requerido (slug) con el texto EXACTO del Zod
schema, el dialog NO cierra y NINGUN upsert sale a la red (espia de
requests); role.es lleno con role.en vacio -> el error especifico del
locale faltante del par BiLang; fecha `2026-13` -> el error de mes exacto;
corregido todo -> el submit guarda OK (cleanup registrado + delete API).
"""

from __future__ import annotations

from api._cv_admin_flows import CvAdminSession
from playwright.sync_api import Request

from ._cv_ui import ACTION_TIMEOUT
from ._cv_ui import card
from ._cv_ui import fill_bilang
from ._cv_ui import fill_field
from ._cv_ui import goto_cv_overview
from ._cv_ui import open_new_entity
from ._cv_ui import open_section
from ._cv_ui import save_entity
from ._cv_ui import select_option
from ._cv_ui import set_niche
from ._cv_ui import ui_slug
from .conftest import CvAdminPage


def test_cv_bilang_validation_ui(
    cv_page: CvAdminPage,
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given el dialog de alta de /cv/experiences con un espia de requests,
    When somete el form vacio, luego con role.en faltante, luego con una
        fecha de mes invalido, y finalmente corregido,
    Then cada submit invalido muestra el mensaje Zod EXACTO sin emitir
        ningun POST de upsert y sin cerrar el dialog, y el submit valido
        guarda y muestra la card. Cero errores de consola.
    """
    # Arrange: espia de upserts de experience que salen a la red.
    page = cv_page.page
    session = cv_admin_session
    slug = ui_slug('valid')
    session.register('experience', slug)
    upsert_requests: list[str] = []

    def _spy(request: Request) -> None:
        if (
            request.url.endswith('/cv')
            and request.method == 'POST'
            and '"action":"upsert-experience"' in (request.post_data or '')
        ):
            upsert_requests.append(request.post_data or '')

    page.on('request', _spy)

    goto_cv_overview(page)
    open_section(page, 'experiences')
    open_new_entity(page)

    # 1. Submit con todo vacio: error del primer campo requerido (slug),
    #    el dialog NO cierra, NINGUN request de upsert salio.
    page.click('[data-testid=cv-form-submit]')
    page.wait_for_selector('text=El slug es obligatorio', timeout=15_000)
    assert (
        page.locator(
            '[data-testid=cv-entity-form-dialog]',
        ).is_visible()
        is True
    )
    assert upsert_requests == []

    # 2. role.es lleno y role.en vacio (resto valido): error especifico
    #    del locale faltante del par BiLang.
    fill_field(page, 'cv-field-slug', slug)
    fill_bilang(page, 'role', 'Ingeniero validacion', '')
    fill_field(page, 'cv-field-company', 'E2E Cvadm UI Corp')
    fill_field(page, 'cv-field-country', 'Chile')
    fill_field(page, 'cv-field-start', '2024-01')
    select_option(page, 'cv-field-seniority', 'senior')
    set_niche(page, 'generic', priority=1)
    page.click('[data-testid=cv-form-submit]')
    role_error = page.locator('[data-testid=bilang-field-role]').get_by_text(
        'Falta el texto en inglés (en)',
    )
    role_error.wait_for(state='visible', timeout=15_000)
    assert upsert_requests == []

    # 3. Fecha con mes invalido: error de formato exacto.
    fill_bilang(page, 'role', 'Ingeniero validacion', 'Validation engineer')
    fill_field(page, 'cv-field-start', '2026-13')
    page.click('[data-testid=cv-form-submit]')
    page.wait_for_selector('text=Mes invalido (01-12)', timeout=15_000)
    assert upsert_requests == []

    # 4. Corregir todo: el submit guarda OK (request 200 + card visible).
    fill_field(page, 'cv-field-start', '2026-01')
    save_entity(page, action='upsert-experience')
    card(page, slug).wait_for(state='visible', timeout=ACTION_TIMEOUT)
    assert len(upsert_requests) == 1

    # Cleanup inmediato via API (ademas del teardown registrado).
    deleted = session.post('delete-experience', {'slug': slug})
    assert deleted.status == 200
    assert cv_page.console_errors == []
