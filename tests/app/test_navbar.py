"""Navbar responsive: dropdown desktop + drawer mobile + breakpoint (AC-3).

Porta `tests/feature/navbar/navbar-breakpoints.spec.ts`:
  - Desktop (1280x800): el trigger del `NicheDropdown` togglea
    `aria-expanded`, cierra al click-outside y al Escape (devolviendo el
    focus al trigger).
  - Mobile (375x667): el hamburger abre el `<dialog>`; la seccion "Otras
    vistas" es un `<details>` cerrado por default que expande al click; al
    reabrir el drawer el `<details>` se resetea a cerrado.
  - Breakpoint resize 1280 -> 375: el dropdown desktop se oculta y el
    hamburger aparece.

Cada escenario fija su viewport via un contexto propio (playwright-python no
tiene `test.use`), creado desde el `browser` de sesion.
"""

from __future__ import annotations

from collections.abc import Callable
from collections.abc import Iterator

from playwright.sync_api import Browser
from playwright.sync_api import Page
import pytest
from shared import browser as browser_tools


_DESKTOP = {'width': 1280, 'height': 800}
_MOBILE = {'width': 375, 'height': 667}


def _page_at(browser: Browser, viewport: dict[str, int]) -> Iterator[Page]:
    context = browser.new_context(viewport=viewport)  # type: ignore[arg-type]
    page = context.new_page()
    try:
        yield page
    finally:
        page.close()
        context.close()


@pytest.fixture
def desktop_page(browser: Browser) -> Iterator[Page]:
    """Pagina con viewport desktop (1280x800) en contexto aislado."""
    yield from _page_at(browser, _DESKTOP)


@pytest.fixture
def mobile_page(browser: Browser) -> Iterator[Page]:
    """Pagina con viewport mobile (375x667) en contexto aislado."""
    yield from _page_at(browser, _MOBILE)


@pytest.mark.app
def test_navbar_desktop_trigger_toggles_aria_expanded(
    desktop_page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """El trigger del dropdown togglea `aria-expanded` y la visibilidad.

    Given el apex en viewport desktop con el menu cerrado,
    When se hace click en el trigger dos veces,
    Then el primer click abre el menu (`aria-expanded=true`, menu visible) y
    el segundo lo cierra (`aria-expanded=false`, menu oculto).
    """
    # Arrange
    browser_tools.goto(desktop_page, f'{subdomain("generic")}/')
    trigger = desktop_page.locator('[data-niche-dropdown-trigger]').first
    menu = desktop_page.locator('[data-niche-dropdown-menu]').first

    # Act + Assert: estado inicial cerrado
    assert trigger.is_visible() is True
    assert menu.is_hidden() is True
    assert trigger.get_attribute('aria-expanded') == 'false'

    # Act + Assert: primer click abre
    trigger.click()
    menu.wait_for(state='visible')
    assert trigger.get_attribute('aria-expanded') == 'true'

    # Act + Assert: segundo click cierra
    trigger.click()
    menu.wait_for(state='hidden')
    assert trigger.get_attribute('aria-expanded') == 'false'


@pytest.mark.app
def test_navbar_desktop_click_outside_closes_menu(
    desktop_page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """Click fuera del menu abierto lo cierra.

    Given el apex en desktop con el dropdown abierto,
    When se hace click en una esquina libre del documento (5, 5),
    Then el menu pasa a oculto.
    """
    # Arrange
    browser_tools.goto(desktop_page, f'{subdomain("generic")}/')
    trigger = desktop_page.locator('[data-niche-dropdown-trigger]').first
    menu = desktop_page.locator('[data-niche-dropdown-menu]').first
    trigger.click()
    menu.wait_for(state='visible')

    # Act
    desktop_page.mouse.click(5, 5)
    menu.wait_for(state='hidden')

    # Assert
    assert menu.is_hidden() is True


@pytest.mark.app
def test_navbar_desktop_escape_closes_and_refocuses_trigger(
    desktop_page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """Escape cierra el menu y devuelve el focus al trigger.

    Given el apex en desktop con el dropdown abierto,
    When se presiona Escape,
    Then el menu se oculta y el trigger recupera el focus.
    """
    # Arrange
    browser_tools.goto(desktop_page, f'{subdomain("generic")}/')
    trigger = desktop_page.locator('[data-niche-dropdown-trigger]').first
    menu = desktop_page.locator('[data-niche-dropdown-menu]').first
    trigger.click()
    menu.wait_for(state='visible')

    # Act
    desktop_page.keyboard.press('Escape')
    menu.wait_for(state='hidden')

    # Assert
    assert menu.is_hidden() is True
    is_focused = trigger.evaluate('el => el === document.activeElement')
    assert is_focused is True


@pytest.mark.app
def test_navbar_mobile_hamburger_opens_drawer_with_details_closed(
    mobile_page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """El hamburger abre el drawer con el `<details>` "Otras vistas" cerrado.

    Given el apex en viewport mobile,
    When se hace click en el hamburger y luego en el summary del `<details>`,
    Then el `<dialog>` es visible, el `<details>` arranca cerrado, tras el
    click queda abierto y renderiza 5 sublinks (uno por niche).
    """
    # Arrange
    browser_tools.goto(mobile_page, f'{subdomain("generic")}/')
    hamburger = mobile_page.locator('[data-mobile-nav-toggle]').first
    assert hamburger.is_visible() is True

    # Act
    hamburger.click()
    dialog = mobile_page.locator('[data-mobile-nav-dialog]').first
    dialog.wait_for(state='visible')
    details = mobile_page.locator('[data-mobile-niche-details]').first

    # Assert: cerrado por default
    assert details.evaluate('el => el.open') is False

    # Act - expandir el details
    details.locator('summary').click()
    mobile_page.wait_for_function(
        'el => el.open === true',
        arg=details.element_handle(),
    )

    # Assert: abierto + 5 sublinks
    assert details.evaluate('el => el.open') is True
    sublinks = details.locator('a.mobile-nav-drawer__sublink')
    assert sublinks.count() == 5


@pytest.mark.app
def test_navbar_mobile_reopen_resets_details_to_closed(
    mobile_page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """Reabrir el drawer resetea el `<details>` a cerrado.

    Given el apex en mobile con el drawer abierto y el `<details>` expandido,
    When se cierra el drawer (boton X) y se reabre,
    Then el `<details>` vuelve al estado cerrado.
    """
    # Arrange
    browser_tools.goto(mobile_page, f'{subdomain("generic")}/')
    hamburger = mobile_page.locator('[data-mobile-nav-toggle]').first
    hamburger.click()
    details = mobile_page.locator('[data-mobile-niche-details]').first
    details.locator('summary').click()
    mobile_page.wait_for_function(
        'el => el.open === true',
        arg=details.element_handle(),
    )

    # Act
    mobile_page.locator('[data-mobile-nav-close]').first.click()
    mobile_page.locator('[data-mobile-nav-dialog]').first.wait_for(
        state='hidden',
    )
    hamburger.click()
    mobile_page.locator('[data-mobile-nav-dialog]').first.wait_for(
        state='visible',
    )

    # Assert
    assert details.evaluate('el => el.open') is False


@pytest.mark.app
def test_navbar_resize_desktop_to_mobile_hides_dropdown_shows_hamburger(
    browser: Browser,
    subdomain: Callable[[str], str],
) -> None:
    """Al cruzar el breakpoint 1280 -> 375 el dropdown se oculta.

    Given el apex en desktop (1280) con el dropdown abierto,
    When se redimensiona el viewport a mobile (375),
    Then el menu del dropdown desktop deja de estar visible y el hamburger
    pasa a estar visible.
    """
    # Arrange
    context = browser.new_context(viewport=_DESKTOP)  # type: ignore[arg-type]
    page = context.new_page()
    try:
        browser_tools.goto(page, f'{subdomain("generic")}/')
        trigger = page.locator('[data-niche-dropdown-trigger]').first
        menu = page.locator('[data-niche-dropdown-menu]').first
        trigger.click()
        menu.wait_for(state='visible')

        # Act
        page.set_viewport_size(_MOBILE)  # type: ignore[arg-type]
        menu.wait_for(state='hidden')

        # Assert
        assert menu.is_hidden() is True
        hamburger = page.locator('[data-mobile-nav-toggle]').first
        hamburger.wait_for(state='visible')
        assert hamburger.is_visible() is True
    finally:
        page.close()
        context.close()
