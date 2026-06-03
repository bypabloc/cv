"""Filtros del CV via query params en las apps con CV (AC-3).

Porta `tests/feature/smoke/cv-filters.spec.ts`: el filter engine
client-side funciona end-to-end sobre las apps desplegadas. `?tech=` filtra
items, el chip/clear actualiza la URL sin full reload, el badge cuenta los
filtros activos, el bundle `cv-filters.js` se sirve, y con JS deshabilitado
el shell de filtros queda oculto con todos los items visibles (fallback
ATS-safe).

Apps con CV (las 5 niches + generic = apex): hub NO tiene CV. Solo chromium
(el toggle de filtros es client-side, no depende del browser engine).
"""

from __future__ import annotations

from collections.abc import Callable

from playwright.sync_api import Browser
from playwright.sync_api import Page
import pytest
from shared import browser as browser_tools


# Apps que renderizan el CV con filtros (hub queda fuera: no tiene CV).
_APPS_WITH_FILTERS = ('generic', 'fintech', 'architect', 'leader', 'vibe')


@pytest.mark.app
def test_cv_filters_tech_query_hides_non_matching_items(
    page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """`?tech=Vue` deja visibles solo los items con esa tech (algunos, no 0).

    Given el home del apex cargado con `?tech=Vue`,
    When el filter engine boota (toggle visible),
    Then la cantidad de items visibles es menor que el total y mayor que 0
    (filtro aplicado, no oculta todo ni nada).
    """
    # Arrange
    browser_tools.goto(page, f'{subdomain("generic")}/?tech=Vue')

    # Act
    browser_tools.wait_selector(page, '[data-filter-toggle]')
    total = page.locator('[data-filterable]').count()
    visible = page.locator('[data-filterable]:not([hidden])').count()

    # Assert
    assert total > 0
    assert 0 < visible < total


@pytest.mark.app
def test_cv_filters_tech_query_shows_badge_count_one(
    page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """`?tech=Vue` muestra el badge contador de filtros activos en `1`.

    Given el home del apex cargado con `?tech=Vue`,
    When el badge de filtros activos boota,
    Then es visible y su texto es exactamente `1` (un filtro activo).
    """
    # Arrange
    browser_tools.goto(page, f'{subdomain("generic")}/?tech=Vue')

    # Act
    browser_tools.wait_selector(page, '[data-filter-count]')
    badge = page.locator('[data-filter-count]').first

    # Assert
    assert badge.is_visible() is True
    assert badge.inner_text() == '1'


@pytest.mark.app
def test_cv_filters_chip_click_updates_url_without_full_reload(
    page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """Click en un chip de tech agrega el query param sin recargar la pagina.

    Given el home del apex con el panel de filtros abierto,
    When se hace click en el primer chip de tech (tras dejar un marcador en
    `window`),
    Then la URL gana `tech=` y el marcador sigue vivo (no hubo full reload).
    """
    # Arrange
    browser_tools.goto(page, f'{subdomain("generic")}/')
    page.locator('[data-filter-toggle]').first.click()
    browser_tools.wait_selector(page, '[data-filter-panel]')
    page.evaluate('() => { window.__filterTestMarker = true }')

    # Act
    page.locator('[data-filter-chip="tech"]').first.click()
    page.wait_for_function(
        '() => window.location.search.includes("tech=")',
        timeout=5_000,
    )

    # Assert
    assert 'tech=' in browser_tools.url_of(page)
    marker = page.evaluate('() => window.__filterTestMarker === true')
    assert marker is True


@pytest.mark.app
def test_cv_filters_clear_all_resets_url_and_items(
    page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """Clear-all quita el query y vuelve a mostrar todos los items.

    Given el home del apex con `?tech=Vue` y el panel abierto,
    When se hace click en el boton clear-all,
    Then la URL pierde `tech=`, todos los items quedan visibles y el badge se
    oculta.
    """
    # Arrange
    browser_tools.goto(page, f'{subdomain("generic")}/?tech=Vue')
    page.locator('[data-filter-toggle]').first.click()
    browser_tools.wait_selector(page, '[data-filter-panel]')

    # Act
    page.locator('[data-filter-clear="all"]').click()
    page.wait_for_function(
        '() => !window.location.search.includes("tech=")',
        timeout=5_000,
    )
    total = page.locator('[data-filterable]').count()
    visible = page.locator('[data-filterable]:not([hidden])').count()

    # Assert
    assert 'tech=' not in browser_tools.url_of(page)
    assert visible == total
    assert page.locator('[data-filter-count]').first.is_hidden() is True


@pytest.mark.app
@pytest.mark.parametrize('niche', _APPS_WITH_FILTERS)
def test_cv_filters_typescript_query_works_across_apps(
    page: Page,
    subdomain: Callable[[str], str],
    niche: str,
) -> None:
    """`?tech=TypeScript` activa el filtro (badge `1`) en cada app con CV.

    Given el home de `{niche}` cargado con `?tech=TypeScript`,
    When el filter engine boota,
    Then el toggle es visible y el badge muestra exactamente `1`.
    """
    # Arrange
    browser_tools.goto(page, f'{subdomain(niche)}/?tech=TypeScript')

    # Act
    browser_tools.wait_selector(page, '[data-filter-toggle]')
    browser_tools.wait_selector(page, '[data-filter-count]')
    badge = page.locator('[data-filter-count]').first

    # Assert
    assert page.locator('[data-filter-toggle]').first.is_visible() is True
    assert badge.inner_text() == '1'


@pytest.mark.app
def test_cv_filters_bundle_is_served_with_javascript(
    page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """`/cv-filters.js` responde 200 con content-type JS y tamano razonable.

    Given la app fintech desplegada,
    When se hace GET de `/cv-filters.js`,
    Then responde 200, content-type de JavaScript y el body pesa entre 1 KB y
    15 KB (el bundle del filter engine).
    """
    # Arrange
    request = page.request

    # Act
    response = request.get(f'{subdomain("fintech")}/cv-filters.js')
    body = response.text()
    content_type = response.headers.get('content-type', '')

    # Assert
    assert response.status == 200
    assert 'javascript' in content_type
    assert 1_000 < len(body) < 15_000


@pytest.mark.app
def test_cv_filters_js_disabled_hides_shell_and_shows_all_items(
    browser: Browser,
    subdomain: Callable[[str], str],
) -> None:
    """Con JS deshabilitado el shell de filtros queda oculto y todo visible.

    Given un contexto de browser con JavaScript deshabilitado,
    When se carga el home del apex,
    Then `[data-filter-bar]` esta presente con el atributo `hidden` (el JS
    nunca lo removio) y todos los `[data-filterable]` quedan visibles
    (fallback ATS-safe: sin JS no se aplica ningun filtro).
    """
    # Arrange
    context = browser.new_context(java_script_enabled=False)
    page = context.new_page()
    try:
        # Act
        page.goto(
            f'{subdomain("generic")}/',
            wait_until='domcontentloaded',
        )
        filter_bar = page.locator('[data-filter-bar]')
        hidden_attr = filter_bar.get_attribute('hidden')
        total = page.locator('[data-filterable]').count()
        visible = page.locator('[data-filterable]:not([hidden])').count()

        # Assert
        assert filter_bar.count() == 1
        assert hidden_attr is not None
        assert total > 0
        assert visible == total
    finally:
        page.close()
        context.close()
