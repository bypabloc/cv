"""Fixtures de los E2E de solo lectura contra PRODUCCION (post).

A diferencia de los modulos `api`/`admin`/`app` (que corren contra dev y
mutan datos), estos tests solo hacen GET a las URLs publicas de
`post.the-full-stack.com`: no autentican ni escriben nada, por eso pueden
correr contra prod. No estan en `testpaths` (el comando `e2e` no los
corre): se lanzan a mano despues de un deploy a main.

    cd tests && ../devtools/.venv/bin/python -m pytest production
"""

from __future__ import annotations

from collections.abc import Iterator
import re

from playwright.sync_api import APIRequestContext
from playwright.sync_api import Browser
from playwright.sync_api import Page
from playwright.sync_api import Playwright
from playwright.sync_api import sync_playwright
import pytest


POST_ORIGIN = 'https://post.the-full-stack.com'

# Una entrada de post en llms.txt: `- [Titulo](https://.../<slug>.md): ...`.
_ENTRY = re.compile(
    r'^- \[(?P<title>[^\]]+)\]\((?P<md>https://[^)]+\.md)\)', re.MULTILINE
)


@pytest.fixture(scope='session')
def playwright_instance() -> Iterator[Playwright]:
    """Playwright de sesion (browser y cliente HTTP comparten el proceso)."""
    with sync_playwright() as instance:
        yield instance


@pytest.fixture(scope='session')
def browser(playwright_instance: Playwright) -> Iterator[Browser]:
    """Chromium headless de sesion."""
    instance = playwright_instance.chromium.launch(headless=True)
    try:
        yield instance
    finally:
        instance.close()


@pytest.fixture
def page(browser: Browser) -> Iterator[Page]:
    """Pagina nueva en un contexto aislado por test."""
    context = browser.new_context()
    test_page = context.new_page()
    try:
        yield test_page
    finally:
        context.close()


@pytest.fixture(scope='session')
def http(playwright_instance: Playwright) -> Iterator[APIRequestContext]:
    """Cliente HTTP de Playwright para los archivos de texto."""
    client = playwright_instance.request.new_context(base_url=POST_ORIGIN)
    try:
        yield client
    finally:
        client.dispose()


@pytest.fixture(scope='session')
def guides(http: APIRequestContext) -> list[dict[str, str]]:
    """Las guias publicadas, leidas de llms.txt (fuente unica del indice).

    Cada item: `title`, `md` (URL del .md) y `html` (URL de la pagina).
    """
    body = http.get('/llms.txt').text()
    return [
        {
            'title': m['title'],
            'md': m['md'],
            'html': m['md'].removesuffix('.md') + '/',
        }
        for m in _ENTRY.finditer(body)
    ]
