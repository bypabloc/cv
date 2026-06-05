"""Fixtures + helpers de flujo del modulo admin (browser, contra desplegado).

Provee el harness para ejercitar los flujos COMPLETOS del panel admin
(`admin.portfolio.{env}.the-full-stack.com`) en un browser real
(playwright-python sync). Las primitivas agnosticas (goto/click/fill/...)
viven en `shared.browser`; los helpers de FLUJO que conocen el DOM y la
auth del admin viven AQUI, como pide el plan (fase D.2).

Auth REAL end-to-end. El submit de los forms de login/register esta gateado
por el widget Turnstile, que en el build DESPLEGADO de dev NO esta en modo
E2E (`NEXT_PUBLIC_E2E_BYPASS=false`): el submit nunca se habilita sin
resolver un challenge humano. Por eso la autenticacion del browser se
bootstrapea por el camino del MAGIC-LINK, que el admin desplegado SI honra
sin Turnstile:

1. Se obtienen tokens REALES del backend (`register.start` -> seed del code
   en Neon -> `register.verify-code` -> access + refresh).
2. Se navega el browser a `/callback#access=...&refresh=...&user_id=...&
   email=...&refresh_exp=...`. El admin decodifica el fragment, persiste los
   tokens y aterriza en el shell autenticado (igual que tras un magic-link).

Asi los flujos autenticados (settings update, sessions revoke, logout) se
ejercitan con backend real + tokens reales + DOM real + mutaciones reales
contra dev.

HERMETICO: ningun valor de secreto (bypass, Neon URL, tokens) se imprime.
CLEANUP: los users sinteticos creados se borran de Neon en el teardown
(respetando `--keep-data`).
"""

from __future__ import annotations

import base64
from collections.abc import Iterator
import json
import os
import secrets
import urllib.parse

from playwright.sync_api import Browser
from playwright.sync_api import Page
import pytest
from shared.auth_support import field
from shared.browser import install_bypass_token
from shared.browser import launch
from shared.config import admin_origin
from shared.config import api_base
from shared.config import synthetic_email
from shared.environment import Environment
from shared.http import HttpClient
from shared.runner import make_body


# Code en alfabeto Crockford (8 chars) que se seedea en Neon para cerrar el
# verify-code. Mismo valor que usa shared.auth_support (no es un secreto: el
# backend solo guarda su hash SHA-256).
_SEED_CODE = 'ABCDEFGH'

# Marcador del shell autenticado (heading de la landing protegida).
_SHELL_MARKER = 'text=Panel de administracion'

# Timeouts (ms) de los waits del browser.
_SHELL_TIMEOUT = 25_000
_NAV_TIMEOUT = 15_000


def _is_headed() -> bool:
    """True si el runner pidio `--headed` (env `E2E_HEADED=1`)."""
    return os.environ.get('E2E_HEADED') == '1'


def _jwt_exp_ms(token: str) -> int:
    """Devuelve el `exp` (epoch ms) de un JWT, decodificando su payload.

    Solo lee el claim (no valida la firma — eso es del backend). El
    `refresh_exp` en ms lo necesita el callback del admin para persistir el
    `refreshExpiry` y que el bootstrap tras reload no expulse la sesion.
    """
    payload = token.split('.')[1]
    payload += '=' * (-len(payload) % 4)
    claims = json.loads(base64.urlsafe_b64decode(payload))
    return int(claims['exp']) * 1000


class AdminAuth:
    """Maquinaria de auth REAL del admin: crea sesiones y las inyecta al DOM.

    Encapsula el backend (`HttpClient` al API Gateway) + el `Environment`
    (seed Neon del code) + el origin del admin. Lleva la lista de emails
    sinteticos creados para el cleanup del teardown.
    """

    def __init__(self, env: Environment, http: HttpClient, origin: str) -> None:
        self._env = env
        self._http = http
        self._origin = origin
        self._bypass = env.bypass_token()
        self.created_emails: list[str] = []

    @property
    def origin(self) -> str:
        """Origin del admin desplegado (base de las URLs del browser)."""
        return self._origin

    def new_email(self, slot: str) -> str:
        """Email sintetico unico (SES simulator), registrado para cleanup."""
        email = synthetic_email('admin', slot)
        self.created_emails.append(email)
        return email

    def create_active_user(self, slot: str) -> tuple[str, str, str, str]:
        """Crea un user active y devuelve `(email, user_id, access, refresh)`.

        Flujo backend REAL: `register.start` (con bypass de Turnstile) ->
        seed del code en Neon -> `register.verify-code`. El user queda active
        con tokens reales emitidos por el Lambda `auth`.
        """
        email = self.new_email(slot)
        start = self._http.post(
            '/auth',
            body=make_body(
                'register', 'start', email=email, cf_turnstile_response='',
            ),
            origin=self._origin,
            bypass_token=self._bypass,
        )
        user_id = field(start.body, 'user_id') or self._env.find_user_id(email)
        temp = field(start.body, 'temp_token')
        self._env.seed_code(
            user_id=user_id, kind='register', plaintext=_SEED_CODE,
        )
        verify = self._http.post(
            '/auth',
            body=make_body(
                'register', 'verify-code', code=_SEED_CODE, temp_token=temp,
            ),
            origin=self._origin,
        )
        access = field(verify.body, 'access_token')
        refresh = field(verify.body, 'refresh_token')
        return email, user_id, access, refresh

    def _login_precheck(self, email: str) -> str | None:
        """`login.check-email` (con bypass) -> temp_token precheck (o None).

        El captcha del flujo de login se resuelve SOLO aqui (check-email);
        `login.start` ya NO valida Turnstile, EXIGE este temp precheck
        (`flow='login'` step=0) en `Authorization`. Mismo patron que el
        harness api (`shared` / `tests/api/_flows.login_precheck`).
        """
        resp = self._http.post(
            '/auth',
            body=make_body(
                'login', 'check-email', email=email, cf_turnstile_response='',
            ),
            origin=self._origin,
            bypass_token=self._bypass,
        )
        return field(resp.body, 'temp_token')

    def fresh_login(self, email: str, user_id: str) -> str:
        """Abre una sesion NUEVA del user via API y devuelve su access token.

        Flujo (modelo de lista de metodos required): `login.check-email`
        (precheck con bypass) -> `login.start` (precheck en Authorization, SIN
        email) -> temp step=2 del checklist -> `login.send-email-code` (con ese
        temp, dispara/regenera la fila `auth_email_codes` de kind login) ->
        seed del code login en Neon -> `login.verify-code`. El user de
        `create_active_user` es passwordless ACTIVE (sin password ni MFA): su
        unico metodo required es 'passwordless' (el email_code), asi que el
        `verify-code` suma ese factor (unico required) y emite tokens directo.

        El `send-email-code` es OBLIGATORIO con el temp step=2: regenera la
        fila del code, por eso el seed debe ir DESPUES. Cada login crea una
        fila en `auth_user_sessions` y emite un access token de una FAMILIA
        PROPIA, independiente de la del browser: el bootstrap-refresh del admin
        (que rota su propia familia y blacklistea su access viejo) NO afecta a
        este token. Se usa para las verificaciones server-side y para seedear
        estado (display_name).
        """
        precheck = self._login_precheck(email)
        start = self._http.post(
            '/auth',
            body=make_body('login', 'start'),
            origin=self._origin,
            bearer=precheck,
        )
        temp = field(start.body, 'temp_token')
        send = self._http.post(
            '/auth',
            body=make_body('login', 'send-email-code', temp_token=temp),
            origin=self._origin,
        )
        # send-email-code puede rotar el temp (rolling); si no lo rota,
        # reutiliza el de login.start.
        temp = field(send.body, 'temp_token') or temp
        self._env.seed_code(user_id=user_id, kind='login', plaintext=_SEED_CODE)
        verify = self._http.post(
            '/auth',
            body=make_body(
                'login', 'verify-code', code=_SEED_CODE, temp_token=temp,
            ),
            origin=self._origin,
        )
        return field(verify.body, 'access_token') or ''

    def open_second_session(self, email: str, user_id: str) -> str:
        """Abre una 2da sesion del user via API (alias semantico de fresh_login).

        Cada login.verify-code crea una fila nueva en `auth_user_sessions`. El
        browser sigue con la 1ra sesion; esta es la 2da, para el test de
        revoke. Devuelve su access token (no se usa en el browser).
        """
        return self.fresh_login(email, user_id)

    def update_display_name(self, access: str, name: str) -> int:
        """Setea el display_name via API (users.profile.update). Devuelve status.

        Se usa para dejar un display_name ESTABLE antes del test de settings:
        con un valor no vacio el ProfileForm no entra en el loop de `reset()`
        que ocurre cuando el campo arranca vacio (user recien creado).
        """
        resp = self._http.post(
            '/users',
            body=make_body('profile', 'update', display_name=name),
            origin=self._origin,
            bearer=access,
        )
        return resp.status

    def server_display_name(self, access: str) -> str | None:
        """display_name actual segun el backend (users.profile.get)."""
        resp = self._http.post(
            '/users',
            body=make_body('profile', 'get'),
            origin=self._origin,
            bearer=access,
        )
        return field(resp.body, 'display_name')

    def mfa_setup_totp(self, access: str) -> tuple[int, str | None]:
        """mfa.setup-totp: devuelve `(status, secret_b32)` para el enroll TOTP."""
        resp = self._http.post(
            '/auth',
            body=make_body('mfa', 'setup-totp'),
            origin=self._origin,
            bearer=access,
        )
        return resp.status, field(resp.body, 'secret_b32')

    def mfa_confirm_totp(self, access: str, code: str) -> int:
        """mfa.confirm-totp: cierra el enroll TOTP con `code`. Devuelve status."""
        resp = self._http.post(
            '/auth',
            body=make_body('mfa', 'confirm-totp', code=code),
            origin=self._origin,
            bearer=access,
        )
        return resp.status

    def login_start_status(self, email: str) -> int:
        """Status de `login.start` para `email` (con su precheck).

        Login unificado (fusion register->login) + modelo de lista required:
        `login.check-email` (precheck con bypass) -> `login.start` con el
        precheck en `Authorization`. Para un email NUEVO el `start` necesita el
        email en el body (alta fusionada: crea el user pending) -> responde 200,
        ya NO 404.
        """
        precheck = self._login_precheck(email)
        resp = self._http.post(
            '/auth',
            body=make_body('login', 'start', email=email),
            origin=self._origin,
            bearer=precheck,
        )
        return resp.status

    def login_check_email(self, email: str) -> dict:
        """Body de `login.check-email` (existencia + has_password, sin metodos).

        Paso 1 del login unificado: NO crea nada. Devuelve `{exists, ...}` (el
        body ya parseado de la `Response`). Para un email no registrado el shape
        es `{exists: false, temp_token}`.
        """
        resp = self._http.post(
            '/auth',
            body=make_body(
                'login', 'check-email', email=email, cf_turnstile_response='',
            ),
            origin=self._origin,
            bypass_token=self._bypass,
        )
        return resp.body if isinstance(resp.body, dict) else {}

    def magic_link_callback_url(self, email: str, user_id: str) -> str:
        """Reconstruye la URL del callback REAL del magic-link de login.

        `login.check-email` (precheck con bypass) -> `login.start` (precheck en
        Authorization, SIN email) -> temp step=2 -> `login.send-email-code`
        (CREA la fila del magic-link de kind login en Neon: `login.start` por si
        solo NO la crea) -> seed de su token -> GET `verify-magic-link`. Para
        este user (passwordless ACTIVE, sin factores required adicionales) el
        backend responde 302 con el `Location` del callback con los tokens en el
        fragment (`/callback#access=...`); si tuviera factores pendientes seria
        `#temp=...&methods=...` (no es el caso de este helper). Devuelve ese
        Location (la URL que el browser navegaria al hacer click en el email).
        """
        precheck = self._login_precheck(email)
        start = self._http.post(
            '/auth',
            body=make_body('login', 'start'),
            origin=self._origin,
            bearer=precheck,
        )
        self._http.post(
            '/auth',
            body=make_body(
                'login', 'send-email-code',
                temp_token=field(start.body, 'temp_token'),
            ),
            origin=self._origin,
        )
        token = secrets.token_urlsafe(24)
        self._env.seed_magic_link(user_id=user_id, kind='login', plaintext=token)
        resp = self._http.get(
            '/auth',
            params={
                'operation': 'login',
                'action': 'verify-magic-link',
                'token': token,
            },
            origin=self._origin,
        )
        return resp.header('location') or ''

    def callback_url(
        self,
        *,
        access: str,
        refresh: str,
        user_id: str,
        email: str,
    ) -> str:
        """URL del callback con los tokens en el fragment hash.

        El admin decodifica `#access=&refresh=&user_id=&email=&refresh_exp=`,
        persiste los tokens y aterriza en el shell. Se incluye `refresh_exp`
        (epoch ms) para que el `refreshExpiry` persista y el bootstrap tras
        reload no expulse la sesion.
        """
        fragment = urllib.parse.urlencode(
            {
                'access': access,
                'refresh': refresh,
                'user_id': user_id,
                'email': email,
                'refresh_exp': str(_jwt_exp_ms(refresh)),
            },
        )
        return f'{self._origin}/callback#{fragment}'


def land_in_shell(page: Page, url: str) -> None:
    """Navega a `url` y espera el shell autenticado del admin.

    Given una URL de callback con tokens validos (o el Location de un
    magic-link),
    When el browser la abre,
    Then el admin decodifica los tokens y renderiza la landing protegida
    ("Panel de administracion").
    """
    page.goto(url, wait_until='load')
    page.wait_for_selector(_SHELL_MARKER, timeout=_SHELL_TIMEOUT)


def nav_via_sidebar(page: Page, label: str, url_glob: str) -> None:
    """Navega dentro del SPA via el link del sidebar (preserva la sesion).

    Given el shell autenticado (access token en memoria),
    When se hace click en el item del sidebar,
    Then la ruta cambia client-side SIN recargar (el access token sobrevive,
    a diferencia de un `goto` que lo perderia al bootstrap).
    """
    page.locator('nav').get_by_role('link', name=label).click()
    page.wait_for_url(url_glob, timeout=_NAV_TIMEOUT)


def logout(page: Page) -> None:
    """Cierra la sesion via la UI real (dropdown del header).

    Given el shell autenticado,
    When se abre el menu de usuario y se hace click en "Cerrar sesion",
    Then el admin llama session.logout, limpia el store y redirige a /login.
    """
    page.get_by_role('button', name='Menu de usuario').click()
    page.get_by_role('menuitem', name='Cerrar sesion').click()
    page.wait_for_url('**/login**', timeout=_NAV_TIMEOUT)


@pytest.fixture(scope='session')
def environment(env: str, aws_profile: str | None) -> Environment:
    """`Environment` del modulo (SSM + Neon + bypass) para el env elegido."""
    return Environment(env, aws_profile=aws_profile)


@pytest.fixture(scope='session')
def admin_url(env: str) -> str:
    """Origin del admin desplegado para el env (base de las URLs del browser)."""
    return admin_origin(env)


@pytest.fixture(scope='session')
def auth(
    env: str,
    environment: Environment,
    keep_data: bool,
) -> Iterator[AdminAuth]:
    """Maquinaria de auth REAL del admin + cleanup de los users creados.

    Crea un `HttpClient` al API Gateway del env y un `AdminAuth` que sabe
    crear sesiones reales. En el teardown borra de Neon todos los users
    sinteticos creados durante la sesion (salvo `--keep-data`).
    """
    http = HttpClient(base_url=api_base(env))
    machine = AdminAuth(environment, http, admin_origin(env))
    try:
        yield machine
    finally:
        if not keep_data and machine.created_emails:
            environment.cleanup_users(machine.created_emails)
        http.close()


@pytest.fixture
def browser() -> Iterator[Browser]:
    """Browser Chromium (headless salvo `--headed` via `E2E_HEADED=1`)."""
    playwright, browser_obj = launch(headless=not _is_headed())
    try:
        yield browser_obj
    finally:
        browser_obj.close()
        playwright.stop()


@pytest.fixture
def page(browser: Browser) -> Iterator[Page]:
    """Pagina en un contexto fresco (cookies/storage limpios por test)."""
    context = browser.new_context()
    page_obj = context.new_page()
    try:
        yield page_obj
    finally:
        context.close()


@pytest.fixture
def bypass_page(browser: Browser, auth: AdminAuth) -> Iterator[Page]:
    """Pagina con el bypass de Turnstile inyectado en `window` (init script).

    El admin desplegado de dev NO esta en modo E2E, asi que el header de
    bypass no se enviaria igual; el bypass aqui es para paridad con el helper
    TS y para escenarios donde el build SI honre el modo E2E. Los flujos
    autenticados NO dependen de el (usan el camino del callback).
    """
    context = browser.new_context()
    page_obj = context.new_page()
    token = auth._bypass
    if token:
        install_bypass_token(page_obj, token)
    try:
        yield page_obj
    finally:
        context.close()


class Flows:
    """Helpers de flujo del admin expuestos como fixture (no como import).

    pytest no expone los simbolos de `conftest.py` como un modulo importable
    (y el repo prohibe `__init__.py` en los dirs de test). Para que los tests
    usen los helpers de flujo sin gimnasia de import, se publican via este
    contenedor de funciones.
    """

    land_in_shell = staticmethod(land_in_shell)
    nav_via_sidebar = staticmethod(nav_via_sidebar)
    logout = staticmethod(logout)


@pytest.fixture(scope='session')
def flows() -> Flows:
    """Helpers de flujo del admin (land_in_shell / nav_via_sidebar / logout)."""
    return Flows()


@pytest.fixture
def logged_in_page(
    page: Page,
    auth: AdminAuth,
) -> Iterator[tuple[Page, str, str]]:
    """Pagina ya autenticada en el shell + `(email, user_id)`.

    Crea un user active REAL, obtiene tokens reales y los inyecta via el
    callback del magic-link: el browser aterriza en el shell autenticado.
    Devuelve la page lista + `(email, user_id)`.

    NO devuelve el access token del callback: el bootstrap del admin rota su
    familia y blacklistea ese access (no deterministico). Los tests que
    necesitan un token de API piden uno NUEVO con `auth.fresh_login(email,
    user_id)` (familia propia, independiente de la del browser).
    """
    email, user_id, access, refresh = auth.create_active_user('shell')
    url = auth.callback_url(
        access=access, refresh=refresh, user_id=user_id, email=email,
    )
    land_in_shell(page, url)
    return page, email, user_id


__all__ = [
    'AdminAuth',
    'Flows',
    'land_in_shell',
    'logout',
    'nav_via_sidebar',
]
