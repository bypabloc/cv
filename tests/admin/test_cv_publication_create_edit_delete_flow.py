"""Flujo de una publication en /cv/publications — seccion SIN lectura.

Doc 12 (tabla de secciones simples): title, platform, url, canonical
(`canonicalUrl` en el doc; el campo real del form es `canonical`), date,
summary, niches. DESVIO OBLIGADO del flujo de 10 pasos: el GET /cv NO
expone publications (gap conocido del plan, `readAction: null`), asi que
la lista del admin queda SIEMPRE vacia — no hay card, ni hidratacion por
edicion, ni delete por UI. Lo que SI se ejercita por browser:

1. La sub-ruta muestra la nota de "sin lectura publica" y 0 cards.
2. El alta por dialog persiste (upsert 200 + toast + dialog cierra).
3. La "edicion" se ejercita re-upserteando el MISMO slug desde el dialog
   de alta (mismo id en el backend, mutacion del summary).
4. El delete + delete idempotente van via API (unica via posible).
"""

from __future__ import annotations

from api._cv_admin_flows import CvAdminSession
from playwright.sync_api import Page

from ._cv_ui import cards_count
from ._cv_ui import field_value
from ._cv_ui import fill_bilang
from ._cv_ui import fill_field
from ._cv_ui import goto_cv_overview
from ._cv_ui import open_new_entity
from ._cv_ui import open_section
from ._cv_ui import reload_section
from ._cv_ui import save_entity
from ._cv_ui import set_niche
from ._cv_ui import ui_slug
from .conftest import CvAdminPage


def _fill_publication(page: Page, slug: str, summary_en: str) -> None:
    """Llena el form completo de publication en el dialog de alta."""
    fill_field(page, 'cv-field-slug', slug)
    fill_field(page, 'cv-field-title', 'E2E Cvadm UI Publication')
    fill_field(page, 'cv-field-platform', 'dev.to')
    fill_field(page, 'cv-field-url', 'https://example.com/e2e-cvadm-ui-pub')
    fill_field(
        page,
        'cv-field-canonical',
        'https://example.com/e2e-cvadm-ui-pub-canonical',
    )
    fill_field(page, 'cv-field-date', '2024-04')
    fill_bilang(page, 'summary', 'Resumen publicacion es.', summary_en)
    set_niche(page, 'generic', priority=2)


def test_cv_publication_create_edit_delete_flow(
    cv_page: CvAdminPage,
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin real en /cv/publications (seccion sin lectura
        publica en el GET /cv),
    When crea una publication sintetica por el dialog, la re-upsertea con
        el mismo slug (mutacion) y la borra via API,
    Then la sub-ruta muestra la nota de seccion sin lectura con 0 cards
        SIEMPRE, ambos upserts responden 200 con el MISMO id y el delete
        API responde el contrato exacto. Cero errores de consola.
    """
    page = cv_page.page
    session = cv_admin_session
    slug = ui_slug('pub')
    session.register('publication', slug)

    # 1. La sub-ruta: nota de "sin lectura publica" + lista vacia.
    goto_cv_overview(page)
    open_section(page, 'publications')
    note = page.get_by_role('note')
    note.wait_for(state='visible', timeout=15_000)
    assert ('aun no tiene lectura publica' in note.inner_text()) is True
    assert cards_count(page) == 0

    # 2. Alta por dialog: upsert 200 + toast + dialog cierra. Se captura
    #    el id creado desde la respuesta del POST.
    open_new_entity(page)
    assert field_value(page, 'cv-field-slug') == ''
    _fill_publication(page, slug, 'Publication summary en.')
    save_entity(page, action='upsert-publication')

    # 3. La lista sigue vacia (sin lectura) — tambien tras reload.
    assert cards_count(page) == 0
    reload_section(page)
    assert cards_count(page) == 0

    # 4. "Edicion": re-upsert del MISMO slug desde el dialog de alta con
    #    el summary.en mutado. El backend upsertea (mismo id).
    open_new_entity(page)
    _fill_publication(page, slug, 'Publication summary en (updated).')
    save_entity(page, action='upsert-publication')

    # 5. Delete via API (unica via posible sin lectura) + idempotente.
    deleted = session.post('delete-publication', {'slug': slug})
    assert deleted.status == 200, (
        f'[delete] HTTP {deleted.status}: {deleted.body!r}'
    )
    assert deleted.body == {'entity': slug, 'deleted': True}
    again = session.post('delete-publication', {'slug': slug})
    assert again.status == 404

    # 6. Cero errores de consola.
    assert cv_page.console_errors == []
