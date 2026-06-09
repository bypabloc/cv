"""Smoke E2E de las 6 apps Astro desplegadas (AC-3).

Porta `tests/feature/smoke/smoke.spec.ts`: cada uno de los 6 subdominios
DESPLEGADOS responde HTTP < 400 al primer load y renderiza al menos el
`body` (no es una pagina de error). Es el smoke minimo de cada Cloudflare
Pages project del niche.

Desviacion vs el spec TS: el sub-caso `services.localhost` ("Servicios del
portfolio") NO tiene equivalente desplegado (es un indice del stack local
nginx), asi que se DESCARTA en este modulo (corre solo contra dev).
"""

from __future__ import annotations

from collections.abc import Callable

from playwright.sync_api import Page
import pytest
from shared import browser as browser_tools


# Los 6 niches DESPLEGADOS (generic = apex del env).
_NICHES = ('generic', 'hub', 'fintech', 'architect', 'leader', 'vibe')


@pytest.mark.app
@pytest.mark.parametrize('niche', _NICHES)
def test_smoke_niche_home_responds_2xx_and_renders_body(
    page: Page,
    subdomain: Callable[[str], str],
    niche: str,
) -> None:
    """Cada subdominio desplegado carga sin error y renderiza el body.

    Given el niche `{niche}` desplegado en el entorno activo,
    When se hace GET de su home `/`,
    Then la respuesta tiene status < 400 y el `<body>` es visible (no es una
    pagina de error de Cloudflare/nginx).
    """
    # Arrange
    url = f'{subdomain(niche)}/'

    # Act
    response = page.goto(url, wait_until='domcontentloaded')

    # Assert
    assert response is not None
    assert response.status < 400
    assert page.locator('body').is_visible() is True


@pytest.mark.app
@pytest.mark.parametrize('niche', _NICHES)
def test_smoke_niche_home_renders_h1(
    page: Page,
    subdomain: Callable[[str], str],
    niche: str,
) -> None:
    """Cada subdominio desplegado renderiza un `<h1>` visible.

    Given el niche `{niche}` desplegado en el entorno activo,
    When se carga su home `/`,
    Then existe un `<h1>` visible (el hero de la app renderizo, no solo un
    shell vacio).
    """
    # Arrange
    url = f'{subdomain(niche)}/'

    # Act
    browser_tools.goto(page, url)
    browser_tools.wait_selector(page, 'h1', state='visible')

    # Assert
    assert page.locator('h1').first.is_visible() is True
