"""Primitivas de UI del editor CV del admin (`/cv/**`) para los E2E browser.

Helpers que conocen el DOM REAL de `admin/src/features/cv-management/`
(data-testid de la Fase 3): navegacion overview/sub-rutas, dialog de
alta/edicion, campos (text/BiLang/Select/Switch), editores de listas
(bilang-list, pair-list, tag-input), picker de niches y el patron
anti-flake de la rule e2e-testing (networkidle + reintento del click si el
island no monto el handler).

Los flujos de NEGOCIO (los 10 pasos del lifecycle de cada entidad) viven
en `_cv_simple_flow.py` y en cada spec; aqui solo primitivas.

El prefijo `_` evita que pytest recolecte este modulo como tests.
"""

from __future__ import annotations

from collections.abc import Callable
import contextlib
import secrets

from playwright.sync_api import Locator
from playwright.sync_api import Page
from playwright.sync_api import Response as PwResponse
from playwright.sync_api import TimeoutError as PwTimeoutError


# Prefijo de TODO dato sintetico creado por los specs UI de cv_admin.
# Arranca con `e2e-cvadm-` para que el teardown del session API (deletes
# registrados + warn de leftovers) lo cubra igual que a los datos del
# modulo api.
TAG_UI = 'e2e-cvadm-ui'

# Timeouts (ms) de los waits del browser contra dev (cold starts lentos).
NAV_TIMEOUT = 25_000
LOAD_TIMEOUT = 35_000
ACTION_TIMEOUT = 30_000


def ui_slug(prefix: str) -> str:
    """Slug sintetico unico `e2e-cvadm-ui-<prefix>-<rand6>`."""
    return f'{TAG_UI}-{prefix}-{secrets.token_hex(3)}'


def cv_admin_response(action: str) -> Callable[[PwResponse], bool]:
    """Predicado para `expect_response`: POST /cv-admin 200 de `action`.

    El api-client del admin serializa el body FLAT sin espacios
    (`JSON.stringify`), por eso el needle es `"action":"<action>"`.
    """
    needle = f'"action":"{action}"'

    def _match(response: PwResponse) -> bool:
        request = response.request
        return (
            request.url.endswith('/cv-admin')
            and request.method == 'POST'
            and needle in (request.post_data or '')
            and response.status == 200
        )

    return _match


# =========================================================================
# Navegacion
# =========================================================================


def goto_cv_overview(page: Page) -> None:
    """Navega al overview `/cv` via el item del sidebar (client-side).

    El item "Gestion CV" es adminOnly: aparece cuando el probe de rol
    resuelve true. NO tiene data-testid propio (desvio del doc 12): se
    localiza por label dentro del `nav` del shell.
    """
    link = page.locator('nav').get_by_role('link', name='Gestion CV')
    link.wait_for(state='visible', timeout=NAV_TIMEOUT)
    link.click()
    page.wait_for_url('**/cv/**', timeout=NAV_TIMEOUT)
    page.wait_for_selector('[data-testid=cv-subnav]', timeout=LOAD_TIMEOUT)


def open_section(page: Page, section: str) -> None:
    """Abre una sub-ruta de LISTA via el sub-nav y espera la lista cargada."""
    page.click(f'[data-testid=cv-subnav-{section}]')
    page.wait_for_url(f'**/cv/{section}/**', timeout=NAV_TIMEOUT)
    wait_section_loaded(page)


def open_profile(page: Page) -> None:
    """Abre `/cv/profile` via el sub-nav y espera el form hidratado."""
    page.click('[data-testid=cv-subnav-profile]')
    page.wait_for_url('**/cv/profile/**', timeout=NAV_TIMEOUT)
    wait_profile_loaded(page)


def settle_network(page: Page, *, timeout: float = 10_000) -> None:
    """networkidle best-effort: NO falla si la red nunca queda idle.

    Contra dev, un request colgado (fallo de red transitorio del container,
    diagnosticado en las corridas previas) puede impedir el networkidle por
    >30s aunque la UI ya este hidratada y con datos (skeleton detached).
    Los waits de selectores son el gate REAL; esto solo agrega margen
    anti-flake cuando la red SI se asienta rapido.
    """
    with contextlib.suppress(PwTimeoutError):
        page.wait_for_load_state('networkidle', timeout=timeout)


def wait_section_loaded(page: Page) -> None:
    """Espera la lista de una seccion: sin skeleton + boton de alta visible."""
    page.wait_for_selector(
        '[data-testid=cv-entity-new]',
        timeout=LOAD_TIMEOUT,
    )
    page.wait_for_selector(
        '[data-testid=cv-section-skeleton]',
        state='detached',
        timeout=LOAD_TIMEOUT,
    )
    settle_network(page)


def wait_profile_loaded(page: Page) -> None:
    """Espera el form del profile hidratado (sin skeleton)."""
    page.wait_for_selector(
        '[data-testid=cv-profile-skeleton]',
        state='detached',
        timeout=LOAD_TIMEOUT,
    )
    page.wait_for_selector('[data-testid=cv-field-name]', timeout=LOAD_TIMEOUT)
    settle_network(page)


def reload_section(page: Page) -> None:
    """Recarga la pagina (rehydrate de sesion) y espera la lista cargada."""
    page.reload(wait_until='load')
    wait_section_loaded(page)


# =========================================================================
# Lista de cards
# =========================================================================


def card(page: Page, slug: str) -> Locator:
    """Locator de la card de la entidad `slug`."""
    return page.locator(f'[data-testid=cv-entity-card][data-slug="{slug}"]')


def cards_count(page: Page) -> int:
    """Cantidad de cards visibles en la lista de la seccion."""
    return page.locator('[data-testid=cv-entity-card]').count()


def dom_slugs(page: Page) -> list[str]:
    """Slugs de las cards en su ORDEN actual del DOM."""
    return page.eval_on_selector_all(
        '[data-testid=cv-entity-card]',
        'cards => cards.map((c) => c.dataset.slug)',
    )


def wait_dom_order(
    page: Page,
    expected: list[str],
    *,
    timeout: float = ACTION_TIMEOUT,
) -> None:
    """Bloquea hasta que el orden DOM de las cards == `expected` exacto."""
    page.wait_for_function(
        """(expected) => {
            const got = Array.from(
                document.querySelectorAll('[data-testid=cv-entity-card]'),
            ).map((c) => c.dataset.slug);
            return JSON.stringify(got) === JSON.stringify(expected);
        }""",
        arg=expected,
        timeout=timeout,
    )


def select_niche_filter(page: Page, label: str) -> None:
    """Cambia el selector de niche de la lista (Radix Select) y espera."""
    page.click('[data-testid=cv-niche-select]')
    page.get_by_role('option', name=label, exact=True).click()
    wait_section_loaded(page)


# =========================================================================
# Dialog de alta / edicion / borrado
# =========================================================================


def _click_until(
    page: Page,
    do_click: Callable[[], None],
    wait_selector: str,
    *,
    attempts: int = 3,
) -> None:
    """Click + espera del efecto, con reintento (anti-flake hidratacion).

    Patron de la rule e2e-testing: si el handler React aun no monto, el
    click no produce efecto; se espera networkidle y se reintenta.
    """
    settle_network(page)
    for attempt in range(1, attempts + 1):
        do_click()
        try:
            page.wait_for_selector(wait_selector, timeout=5_000)
        except PwTimeoutError:
            if attempt == attempts:
                raise
            settle_network(page)
            continue
        return


def open_new_entity(page: Page) -> None:
    """Abre el dialog de alta (boton "Nueva entrada")."""
    _click_until(
        page,
        lambda: page.click('[data-testid=cv-entity-new]'),
        '[data-testid=cv-entity-form-dialog]',
    )


def open_edit_entity(page: Page, slug: str) -> None:
    """Abre el dialog de edicion de la card `slug`."""
    _click_until(
        page,
        lambda: (
            card(page, slug).locator('[data-testid=cv-entity-edit]').click()
        ),
        '[data-testid=cv-entity-form-dialog]',
    )


def close_dialog(page: Page) -> None:
    """Cierra el dialog SIN guardar (Escape -> onOpenChange(false))."""
    page.keyboard.press('Escape')
    page.wait_for_selector(
        '[data-testid=cv-entity-form-dialog]',
        state='hidden',
        timeout=ACTION_TIMEOUT,
    )


def save_entity(page: Page, *, action: str) -> None:
    """Guarda el form del dialog y espera exito (200 + toast + cierre)."""
    with page.expect_response(
        cv_admin_response(action),
        timeout=ACTION_TIMEOUT,
    ):
        page.click('[data-testid=cv-form-submit]')
    page.wait_for_selector('text=Cambios guardados', timeout=ACTION_TIMEOUT)
    page.wait_for_selector(
        '[data-testid=cv-entity-form-dialog]',
        state='hidden',
        timeout=ACTION_TIMEOUT,
    )


def save_profile(page: Page) -> None:
    """Guarda el form del profile (sin dialog) y espera exito (200 + toast)."""
    with page.expect_response(
        cv_admin_response('upsert-profile'),
        timeout=ACTION_TIMEOUT,
    ):
        page.click('[data-testid=cv-form-submit]')
    page.wait_for_selector('text=Cambios guardados', timeout=ACTION_TIMEOUT)


def delete_entity(page: Page, slug: str, *, action: str) -> None:
    """Borra la card `slug` con su AlertDialog de confirmacion."""
    _click_until(
        page,
        lambda: (
            card(page, slug).locator('[data-testid=cv-entity-delete]').click()
        ),
        '[data-testid=cv-entity-delete-confirm]',
    )
    with page.expect_response(
        cv_admin_response(action),
        timeout=ACTION_TIMEOUT,
    ):
        page.click('[data-testid=cv-entity-delete-confirm]')
    page.wait_for_selector(
        '[data-testid=cv-entity-delete-confirm]',
        state='hidden',
        timeout=ACTION_TIMEOUT,
    )
    card(page, slug).wait_for(state='detached', timeout=ACTION_TIMEOUT)


# =========================================================================
# Campos del form
# =========================================================================


def fill_field(page: Page, testid: str, value: str) -> None:
    """Llena un Input/Textarea localizado por data-testid."""
    page.fill(f'[data-testid={testid}]', value)


def field_value(page: Page, testid: str) -> str:
    """Valor actual de un Input/Textarea localizado por data-testid."""
    return page.input_value(f'[data-testid={testid}]')


def fill_bilang(page: Page, name: str, es: str, en: str) -> None:
    """Llena el par BiLang `<name>` (inputs bilang-<name>-es / -en)."""
    page.fill(f'[data-testid=bilang-{name}-es]', es)
    page.fill(f'[data-testid=bilang-{name}-en]', en)


def bilang_values(page: Page, name: str) -> tuple[str, str]:
    """Valores (es, en) actuales del par BiLang `<name>`."""
    return (
        page.input_value(f'[data-testid=bilang-{name}-es]'),
        page.input_value(f'[data-testid=bilang-{name}-en]'),
    )


def select_option(page: Page, trigger_testid: str, value: str) -> None:
    """Elige `value` en un Radix Select (click trigger + option exacta)."""
    page.click(f'[data-testid={trigger_testid}]')
    page.get_by_role('option', name=value, exact=True).click()


def select_value(page: Page, trigger_testid: str) -> str:
    """Texto visible del trigger de un Radix Select (el value elegido)."""
    return page.inner_text(f'[data-testid={trigger_testid}]')


def set_switch(page: Page, testid: str, *, on: bool) -> None:
    """Deja el Radix Switch en el estado `on` pedido (idempotente)."""
    if switch_checked(page, testid) != on:
        page.click(f'[data-testid={testid}]')


def switch_checked(page: Page, testid: str) -> bool:
    """True si el Radix Switch esta encendido (aria-checked)."""
    state = page.get_attribute(f'[data-testid={testid}]', 'aria-checked')
    return state == 'true'


# =========================================================================
# Editor de listas paralelas es/en (bilang-list-editor)
# =========================================================================


def _bilang_block(page: Page, name: str):
    return page.locator(f'[data-testid=bilang-list-{name}]')


def add_bilang_item(page: Page, name: str, es: str, en: str) -> None:
    """Agrega una fila al editor `<name>` y la llena (es, en)."""
    block = _bilang_block(page, name)
    before = block.locator('[data-testid=bilang-item-row]').count()
    block.locator('[data-testid=bilang-item-add]').click()
    row = block.locator('[data-testid=bilang-item-row]').nth(before)
    row.locator('[data-testid=bilang-item-es]').fill(es)
    row.locator('[data-testid=bilang-item-en]').fill(en)


def move_bilang_item_up(page: Page, name: str, index: int) -> None:
    """Sube la fila `index` del editor `<name>` una posicion."""
    row = (
        _bilang_block(page, name)
        .locator(
            '[data-testid=bilang-item-row]',
        )
        .nth(index)
    )
    row.locator('[data-testid=bilang-item-up]').click()


def remove_bilang_item(page: Page, name: str, index: int) -> None:
    """Elimina la fila `index` del editor `<name>`."""
    row = (
        _bilang_block(page, name)
        .locator(
            '[data-testid=bilang-item-row]',
        )
        .nth(index)
    )
    row.locator('[data-testid=bilang-item-remove]').click()


def bilang_list_values(
    page: Page,
    name: str,
) -> tuple[list[str], list[str]]:
    """Listas (es, en) actuales del editor `<name>` en su orden visual."""
    block = _bilang_block(page, name)
    es = [
        item.input_value()
        for item in block.locator('[data-testid=bilang-item-es]').all()
    ]
    en = [
        item.input_value()
        for item in block.locator('[data-testid=bilang-item-en]').all()
    ]
    return es, en


# =========================================================================
# Editor de pares {key, value} (pair-list-editor: cv-link / cv-metric)
# =========================================================================


def _pair_block(page: Page, prefix: str):
    return page.locator(f'[data-testid={prefix}-list]')


def add_pair(page: Page, prefix: str, key: str, value: str) -> None:
    """Agrega una fila {key, value} al editor `prefix` y la llena."""
    block = _pair_block(page, prefix)
    before = block.locator(f'[data-testid={prefix}-row]').count()
    block.locator(f'[data-testid={prefix}-add]').click()
    row = block.locator(f'[data-testid={prefix}-row]').nth(before)
    row.locator(f'[data-testid={prefix}-key]').fill(key)
    row.locator(f'[data-testid={prefix}-value]').fill(value)


def move_pair_up(page: Page, prefix: str, index: int) -> None:
    """Sube la fila `index` del editor `prefix` una posicion."""
    row = (
        _pair_block(page, prefix)
        .locator(
            f'[data-testid={prefix}-row]',
        )
        .nth(index)
    )
    row.locator(f'[data-testid={prefix}-up]').click()


def remove_pair(page: Page, prefix: str, index: int) -> None:
    """Elimina la fila `index` del editor `prefix`."""
    row = (
        _pair_block(page, prefix)
        .locator(
            f'[data-testid={prefix}-row]',
        )
        .nth(index)
    )
    row.locator(f'[data-testid={prefix}-remove]').click()


def pair_values(page: Page, prefix: str) -> list[tuple[str, str]]:
    """Pares (key, value) actuales del editor `prefix` en orden visual."""
    block = _pair_block(page, prefix)
    rows = block.locator(f'[data-testid={prefix}-row]').all()
    return [
        (
            row.locator(f'[data-testid={prefix}-key]').input_value(),
            row.locator(f'[data-testid={prefix}-value]').input_value(),
        )
        for row in rows
    ]


# =========================================================================
# Tag input (chips con sugerencias del catalogo)
# =========================================================================


def _tag_block(page: Page, name: str):
    return page.locator(f'[data-testid=tag-input-{name}]')


def add_tag_from_suggestion(page: Page, name: str, text: str) -> None:
    """Tipea `text` y elige la sugerencia EXACTA del catalogo (autocomplete)."""
    block = _tag_block(page, name)
    block.locator(f'[data-testid=tag-input-{name}-field]').fill(text)
    suggestion = block.locator(
        f'[data-testid=tag-suggestion][data-value="{text}"]',
    )
    suggestion.wait_for(state='visible', timeout=ACTION_TIMEOUT)
    suggestion.click()


def add_tag_new(page: Page, name: str, text: str) -> None:
    """Crea un tag NUEVO (texto libre + boton agregar)."""
    block = _tag_block(page, name)
    block.locator(f'[data-testid=tag-input-{name}-field]').fill(text)
    block.locator('[data-testid=tag-add]').click()


def remove_tag(page: Page, name: str, value: str) -> None:
    """Elimina el chip `value` del tag input `<name>`."""
    chip = _tag_block(page, name).locator(
        f'[data-testid=tag-chip][data-value="{value}"]',
    )
    chip.locator('[data-testid=tag-chip-remove]').click()


def move_tag_up(page: Page, name: str, value: str) -> None:
    """Sube el chip `value` una posicion (tag input reorderable)."""
    chip = _tag_block(page, name).locator(
        f'[data-testid=tag-chip][data-value="{value}"]',
    )
    chip.locator('[data-testid=tag-chip-up]').click()


def move_tag_down(page: Page, name: str, value: str) -> None:
    """Baja el chip `value` una posicion (tag input reorderable)."""
    chip = _tag_block(page, name).locator(
        f'[data-testid=tag-chip][data-value="{value}"]',
    )
    chip.locator('[data-testid=tag-chip-down]').click()


def tag_values(page: Page, name: str) -> list[str]:
    """Tags actuales del input `<name>` en su orden visual."""
    return [
        chip.get_attribute('data-value') or ''
        for chip in _tag_block(page, name)
        .locator('[data-testid=tag-chip]')
        .all()
    ]


# =========================================================================
# Picker de niches + prioridad
# =========================================================================


def set_niche(page: Page, slug: str, *, priority: int | None = None) -> None:
    """Marca el niche `slug` y (si aplica) setea su prioridad."""
    page.click(f'[data-testid=niche-checkbox-{slug}]')
    if priority is not None:
        page.fill(f'[data-testid=niche-priority-{slug}]', str(priority))


def unset_niche(page: Page, slug: str) -> None:
    """Desmarca el niche `slug`."""
    page.click(f'[data-testid=niche-checkbox-{slug}]')


def niche_checked(page: Page, slug: str) -> bool:
    """True si el checkbox del niche `slug` esta marcado."""
    state = page.get_attribute(
        f'[data-testid=niche-checkbox-{slug}]',
        'data-state',
    )
    return state == 'checked'


def niche_priority_value(page: Page, slug: str) -> str:
    """Valor actual del input de prioridad del niche `slug`."""
    return page.input_value(f'[data-testid=niche-priority-{slug}]')
