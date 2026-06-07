"""Hub cards -> hrefs derivados del entorno + navegacion cross-subdominio.

Porta `tests/feature/smoke/hub-links.spec.ts`: las 5 cards del hub generan
hrefs absolutos al subdominio del env activo y el click lleva al sitio
correspondiente con HTTP < 400. Cubre AC-3 (env-driven site URLs).

Contra DESPLEGADO los hrefs son las URLs reales del Cloudflare Pages project
de cada niche (`https://{niche}.portfolio.{env}.the-full-stack.com`,
`generic` -> apex), identicas a `shared.config.niche_origin`.
"""

from __future__ import annotations

from collections.abc import Callable

from playwright.sync_api import Page
import pytest
from shared import browser as browser_tools


# Las 5 cards de niche del hub (generic resuelve al apex del env).
_NICHE_CARDS = ('fintech', 'architect', 'leader', 'vibe', 'generic')


@pytest.mark.app
def test_hub_renders_five_niche_cards(
    page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """El hub renderiza exactamente 5 anchors de card con data-niche.

    Given el hub desplegado abierto,
    When se inspeccionan los anchors `a.hub-card[data-niche]`,
    Then hay exactamente 5 (una card por niche del selector).
    """
    # Arrange
    browser_tools.goto(page, f'{subdomain("hub")}/')

    # Act
    count = page.locator('a.hub-card[data-niche]').count()

    # Assert
    assert count == 5


@pytest.mark.app
@pytest.mark.parametrize('niche', _NICHE_CARDS)
def test_hub_card_href_points_to_env_subdomain(
    page: Page,
    subdomain: Callable[[str], str],
    niche: str,
) -> None:
    """El href de cada card apunta al subdominio desplegado del env activo.

    Given el hub desplegado abierto,
    When se lee el href de `a.hub-card[data-niche={niche}]`,
    Then es exactamente la URL desplegada del niche para el env actual
    (`niche_origin(niche, env)`), sin trailing slash.
    """
    # Arrange
    browser_tools.goto(page, f'{subdomain("hub")}/')
    expected = subdomain(niche)

    # Act
    href = page.locator(
        f'a.hub-card[data-niche="{niche}"]',
    ).get_attribute('href')

    # Assert
    assert href == expected


@pytest.mark.app
def test_hub_card_fintech_navigates_to_fintech_2xx(
    page: Page,
    subdomain: Callable[[str], str],
) -> None:
    """Navegar al href de la card fintech aterriza en fintech con HTTP < 400.

    Given el hub desplegado abierto,
    When se lee el href de la card fintech y se navega a el,
    Then la respuesta tiene status < 400 y la URL final contiene el origin
    desplegado de fintech.
    """
    # Arrange
    browser_tools.goto(page, f'{subdomain("hub")}/')
    expected_fintech = subdomain('fintech')
    href = page.locator(
        'a.hub-card[data-niche="fintech"]',
    ).get_attribute('href')
    assert href is not None

    # Act
    response = page.goto(href, wait_until='domcontentloaded')

    # Assert
    assert response is not None
    assert response.status < 400
    assert expected_fintech in browser_tools.url_of(page)
