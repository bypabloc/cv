"""Harness de browser (playwright-python, sync API) para los E2E.

Reemplaza `tests/feature/fixtures/index.ts` + `helpers/{screenshot,
inspect-overlay}.ts`: funciones modulares para arrancar un browser,
navegar, interactuar con el DOM, instalar el bypass de Turnstile, capturar
las requests de tracking y tomar screenshots. Lo usan los modulos `admin`
y `app`.

Se elige la **sync API** de Playwright (no la async) por simplicidad de
composicion con pytest: cada fixture/test es lineal, sin `await`.

Los helpers de FLUJO del admin (login via formulario, logout) NO viven
aqui: dependen del DOM concreto del admin (selectores de los inputs,
labels, botones del LoginForm) y por eso se implementan en
`tests/admin/conftest.py`, con conocimiento de ese DOM. Aqui solo viven
las primitivas agnosticas (goto/click/fill/...) sobre las que esos flujos
se construyen.
"""

from __future__ import annotations

import json
from typing import Any

from playwright.sync_api import Browser
from playwright.sync_api import Page
from playwright.sync_api import Route
from playwright.sync_api import sync_playwright


# Nombre de la variable global que el admin lee para el bypass de Turnstile.
_BYPASS_GLOBAL = '__E2E_BYPASS_TOKEN__'

# Timeout (ms) para screenshots fullPage de paginas largas (CV) con
# view-transitions, alineado con el helper TS original.
_SCREENSHOT_TIMEOUT_MS = 30_000


def launch(*, headless: bool = True) -> tuple[Any, Browser]:
    """Arranca Playwright + un browser Chromium y los devuelve.

    Given que un test necesita un browser real,
    When llama launch(),
    Then devuelve `(playwright, browser)`: el browser para abrir paginas y
    el handle de playwright para cerrarlo despues con `playwright.stop()`.

    El caller es responsable de cerrar ambos (`browser.close()` +
    `playwright.stop()`), tipicamente en el teardown de una fixture.
    """
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless)
    return playwright, browser


def new_page(
    browser: Browser,
    *,
    install_bypass: bool = False,
    bypass_token: str | None = None,
) -> Page:
    """Abre una pagina nueva en un contexto fresco (cookies/storage limpios).

    Given un browser ya arrancado,
    When se pide una pagina nueva,
    Then crea un BrowserContext aislado y su Page. Si `install_bypass` es
    True y hay `bypass_token`, lo inyecta en `window.<global>` ANTES de que
    cargue cualquier script (via add_init_script), igual que el helper TS
    `installBypass`.
    """
    context = browser.new_context()
    page = context.new_page()
    if install_bypass and bypass_token:
        install_bypass_token(page, bypass_token)
    return page


def goto(page: Page, url: str) -> None:
    """Navega a `url` y espera el evento `load`.

    Given una pagina y una URL absoluta,
    When se navega,
    Then espera a que el documento dispare `load` (recursos principales
    cargados) antes de devolver.
    """
    page.goto(url, wait_until='load')


def click(page: Page, selector: str) -> None:
    """Click sobre el primer elemento que matchea `selector`.

    Given un selector visible/clickeable,
    When se hace click,
    Then Playwright espera a que sea accionable y dispara el click.
    """
    page.click(selector)


def fill(page: Page, selector: str, value: str) -> None:
    """Llena un input/textarea con `value`.

    Given un campo de formulario,
    When se llena,
    Then limpia el campo y escribe `value` (focus + set value + input event).
    """
    page.fill(selector, value)


def wait_selector(
    page: Page,
    selector: str,
    *,
    state: str = 'visible',
) -> None:
    """Espera a que `selector` alcance `state` (visible|attached|hidden|...).

    Given un selector que aparece de forma asincrona,
    When se espera,
    Then bloquea hasta que el elemento llega al estado pedido (o timeout).
    """
    page.wait_for_selector(selector, state=state)  # type: ignore[arg-type]


def text_of(page: Page, selector: str) -> str:
    """Texto visible (inner_text) del primer elemento de `selector`.

    Given un selector presente,
    When se pide su texto,
    Then devuelve el `inner_text` (texto renderizado, sin tags).
    """
    return page.inner_text(selector)


def url_of(page: Page) -> str:
    """URL actual de la pagina.

    Given una pagina ya navegada (incluido tras redirects client-side),
    When se consulta,
    Then devuelve `page.url` (la URL efectiva del documento).
    """
    return page.url


def install_bypass_token(page: Page, token: str) -> None:
    """Inyecta el bypass de Turnstile en `window.<global>` (add_init_script).

    Given un token de bypass Ed25519 firmado,
    When se instala,
    Then lo setea en `window.__E2E_BYPASS_TOKEN__` ANTES de que corra
    cualquier script de la pagina (add_init_script aplica en CADA navegacion
    del contexto). El admin lo lee de ahi y lo manda en el header
    `X-Turnstile-Bypass-Token`. Espejo de `installBypass` del fixture TS.
    """
    page.add_init_script(
        f'window.{_BYPASS_GLOBAL} = {json.dumps(token)};',
    )


# Alias corto con la firma pedida en el plan (03-fase-shared A.3).
def install_bypass(page: Page, token: str) -> None:
    """Alias de `install_bypass_token` (firma del plan A.3)."""
    install_bypass_token(page, token)


def disable_send_beacon(page: Page) -> None:
    """Fuerza el fallback `fetch` del tracking sobreescribiendo sendBeacon.

    Given que el frontend prefiere `navigator.sendBeacon` para `POST /track`
    (que Playwright NO expone como request interceptable con su body),
    When se deshabilita sendBeacon ANTES de cargar la pagina,
    Then `track-event.ts` cae al fallback `fetch(...)` keepalive, cuyo
    `postData` SI es visible para `page.route('**/track')` / `capture_track`.
    Implementado con add_init_script (corre en cada navegacion).
    """
    page.add_init_script(
        # Define la propiedad como undefined: el guard `navigator.sendBeacon`
        # del frontend (`typeof navigator.sendBeacon`) cae al `fetch`.
        'try {'
        " Object.defineProperty(navigator, 'sendBeacon',"
        ' { value: undefined, configurable: true });'
        '} catch (e) { /* algunos browsers no permiten redefinir */ }',
    )


class TrackCapturer:
    """Acumula los payloads JSON de los `POST /track` interceptados.

    Cada request a `**/track` se intercepta con `page.route`: su `post_data`
    (JSON serializado por el frontend) se parsea y se guarda en `payloads`,
    y se responde 204 (lo que el backend real devuelve) para no salir a la
    red. Si el body no es JSON valido, se guarda el texto crudo bajo la key
    `_raw`.
    """

    def __init__(self) -> None:
        self.payloads: list[dict[str, Any]] = []

    def _handle(self, route: Route) -> None:
        request = route.request
        raw = request.post_data
        if raw:
            try:
                self.payloads.append(json.loads(raw))
            except (json.JSONDecodeError, ValueError):
                self.payloads.append({'_raw': raw})
        route.fulfill(status=204, body='')

    @property
    def count(self) -> int:
        """Cantidad de requests `/track` capturadas."""
        return len(self.payloads)


def capture_track(page: Page) -> TrackCapturer:
    """Intercepta `POST /track` y acumula sus payloads (responde 204).

    Given una pagina que va a emitir tracking,
    When se instala el capturador,
    Then registra una ruta `**/track` que parsea el body de cada request,
    lo guarda en el `TrackCapturer` devuelto y responde 204 sin salir a la
    red. Espejo de `captureTrackRequests` del helper TS. Usar junto con
    `disable_send_beacon` para garantizar que el body sea visible.
    """
    capturer = TrackCapturer()
    page.route('**/track', capturer._handle)
    return capturer


def screenshot(page: Page, path: str, *, full_page: bool = True) -> None:
    """Guarda un screenshot PNG de la pagina en `path`.

    Given una pagina renderizada,
    When se toma el screenshot,
    Then escribe el PNG en `path` (timeout amplio para fullPage de paginas
    largas con view-transitions). Espejo de `captureScreenshot` del helper
    TS, sin el `attach` al reporte (los PNG van a `tests/results/`,
    gitignored).
    """
    page.screenshot(
        path=path,
        full_page=full_page,
        timeout=_SCREENSHOT_TIMEOUT_MS,
    )
