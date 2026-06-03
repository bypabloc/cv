"""Fixtures del modulo `app`: las 6 apps Astro DESPLEGADAS (browser).

Reemplaza `tests/feature/fixtures/index.ts`: provee un `browser` de sesion
(playwright-python sync), una `page` fresca por test y un helper
`subdomain(niche)` que resuelve la URL desplegada del niche segun `--env`.

A diferencia del modulo `admin`, el modulo `app` NO requiere auth dura (no
muta datos, no autentica): ningun test escribe en el backend desplegado.
Los tests de tracking/funnel SIEMPRE interceptan `POST /track` con
`page.route` (responden 204 local), por lo que NUNCA dejan pasar el request
real (ver `shared.browser.capture_track`).
"""

from __future__ import annotations

from collections.abc import Callable
from collections.abc import Iterator

from playwright.sync_api import Browser
from playwright.sync_api import Page
import pytest
from shared import browser as browser_tools
from shared import config


def pytest_configure(config: pytest.Config) -> None:
    """Registra el marker `screenshots` (subconjunto lento del modulo `app`).

    Given que `test_screenshots.py` genera ~54 PNG y tarda,
    When pytest arranca,
    Then registra el marker `screenshots` para poder excluir esos tests
    (`-m 'not screenshots'`) sin disparar el warning de marker no registrado.
    El marker `app` global vive en `tests/pyproject.toml`.
    """
    config.addinivalue_line(
        'markers',
        'screenshots: capturas multi-viewport (lento, solo chromium)',
    )


@pytest.fixture(scope='session')
def browser() -> Iterator[Browser]:
    """Browser Chromium de sesion para todo el modulo `app`.

    Given que los tests del modulo necesitan un browser real,
    When se inicia la sesion de pytest,
    Then arranca Playwright + Chromium una sola vez y los cierra en el
    teardown (`browser.close()` + `playwright.stop()`), amortizando el costo
    de arranque entre todos los tests.
    """
    playwright, instance = browser_tools.launch(headless=True)
    try:
        yield instance
    finally:
        instance.close()
        playwright.stop()


@pytest.fixture
def page(browser: Browser) -> Iterator[Page]:
    """Pagina nueva en un contexto aislado (cookies/storage limpios) por test.

    Given un browser de sesion,
    When un test pide una `page`,
    Then crea un BrowserContext fresco y su Page, y los cierra al terminar el
    test (aislamiento total entre tests: ni storage ni cookies se filtran).
    """
    context = browser.new_context()
    test_page = context.new_page()
    try:
        yield test_page
    finally:
        test_page.close()
        context.close()


@pytest.fixture
def subdomain(env: str) -> Callable[[str], str]:
    """Helper que devuelve la URL desplegada de un niche para el env activo.

    Given el entorno de deploy elegido (`--env`),
    When se invoca `subdomain('fintech')`,
    Then devuelve `https://fintech.portfolio.<env>.the-full-stack.com`;
    `subdomain('generic')` resuelve al apex del env. Espejo de `subdomainUrl`
    del fixture TS, pero contra los subdominios DESPLEGADOS (no localhost).
    """

    def resolve(niche: str) -> str:
        return config.niche_origin(niche, env)

    return resolve
