"""Login multi-factor (password + webauthn) end-to-end por el checklist real.

Reproduce el flujo donde un user tiene DOS factores `required`: `password` y
`webauthn` (passkey). El login debe completarse cuando AMBOS estan satisfechos
(en cualquier orden) y redirigir al shell. Hoy NO converge: el factor webauthn
arranca un sub-flujo aislado (`webauthn.login-verify` hardcodea
`satisfied=['webauthn']` y no recibe el temp_token rolling del checklist), asi
que `mfa_complete` nunca llega a true y el checklist se queda sin redirigir.

Corre contra el admin DESPLEGADO (`admin.portfolio.{env}.the-full-stack.com`),
NO el local: el ceremony WebAuthn exige que el RP ID del backend
(`portfolio.dev.*`) sea un sufijo registrable del dominio de la pagina — solo
se cumple en el dominio desplegado (en admin.localhost el browser lanza
SecurityError antes del Virtual Authenticator, que NO salta esa validacion).
El form de login se automatiza porque el build de dev tiene
`NEXT_PUBLIC_E2E_BYPASS=true` (GH Variable del environment dev): el widget
Turnstile no se renderiza y el bypass token Ed25519 inyectado en
`window.__E2E_BYPASS_TOKEN__` viaja en el header `X-Turnstile-Bypass-Token`,
que el backend dev acepta.

Setup (orden importante): la password es `required` por server_default. Por eso
se entra al shell con un login solo-password (unico factor) ANTES de registrar
el passkey; recien despues se marca el passkey `required` para llegar al
escenario de 2 factores.
"""

from __future__ import annotations

import base64
from collections.abc import Iterator
import json
import urllib.parse

from playwright.sync_api import Browser
from playwright.sync_api import Page
import pytest
from shared.auth_support import STRONG_PASSWORD
from shared.auth_support import create_active_user_with_password
from shared.auth_support import login_with_password
from shared.browser import add_virtual_authenticator
from shared.browser import install_bypass_token
from shared.config import admin_origin
from shared.config import api_base
from shared.environment import Environment
from shared.http import HttpClient
from shared.runner import make_body

_SHELL_MARKER = 'text=Panel de administracion'


def _callback_url(
    *, admin: str, access: str, refresh: str, user_id: str, email: str,
) -> str:
    """URL del callback del admin con los tokens en el fragment hash."""
    payload = refresh.split('.')[1]
    payload += '=' * (-len(payload) % 4)
    refresh_exp = int(json.loads(base64.urlsafe_b64decode(payload))['exp']) * 1000
    frag = urllib.parse.urlencode(
        {
            'access': access,
            'refresh': refresh,
            'user_id': user_id,
            'email': email,
            'refresh_exp': str(refresh_exp),
        },
    )
    return f'{admin}/callback#{frag}'


@pytest.fixture
def mf_setup(
    browser: Browser,
    environment: Environment,
    env: str,
    auth,
) -> Iterator[tuple[Page, str, str]]:
    """Prepara un user con password+webauthn required; entrega `(page, email, admin)`.

    El `page` queda en una sesion LIMPIA (sin cookies) listo para el login
    real; el Virtual Authenticator ya tiene la passkey registrada (persiste en
    el BrowserContext). El cleanup del user lo hace el teardown del fixture
    `auth` (registra el email en `created_emails`). `admin` es el origin del
    admin desplegado del env.
    """
    admin = admin_origin(env)
    context = browser.new_context()
    page = context.new_page()
    bypass = environment.bypass_token() or ''
    if bypass:
        install_bypass_token(page, bypass)
    add_virtual_authenticator(page)
    http = HttpClient(base_url=api_base(env))
    origin = api_base(env)
    try:
        # 1) User active CON password (la password queda required por default).
        email = auth.new_email('multifactor')
        user_id = create_active_user_with_password(
            http, environment, origin, email, bypass,
        )
        assert user_id is not None, 'no se creo el user con password'

        # 2) Login solo-password (unico factor required aun) -> tokens reales.
        access, refresh = login_with_password(http, origin, email, bypass)
        assert access and refresh, 'login solo-password no emitio tokens'

        # 3) Browser al shell via callback -> registrar el passkey.
        page.goto(
            _callback_url(
                admin=admin, access=access, refresh=refresh,
                user_id=user_id, email=email,
            ),
            wait_until='load',
        )
        page.wait_for_selector(_SHELL_MARKER, timeout=25_000)
        page.locator('nav').get_by_role('link', name='Configuracion').click()
        page.get_by_role('link', name='Seguridad').click()
        page.wait_for_url('**/settings/security**', timeout=15_000)
        page.get_by_role('button', name='Agregar passkey').click()
        page.wait_for_selector('text=Passkey registrado', timeout=30_000)
        assert environment.count_webauthn_credentials(user_id) == 1

        # 4) Marcar el passkey required (necesita su credential_id = UUID PK).
        creds = http.post(
            '/auth',
            body=make_body('webauthn', 'list-credentials'),
            origin=origin,
            bearer=access,
        )
        cred_id = creds.body['credentials'][0]['credential_id']
        wa_req = http.post(
            '/auth',
            body=make_body(
                'webauthn', 'set-required', credential_id=cred_id, required=True,
            ),
            origin=origin,
            bearer=access,
        )
        assert wa_req.status == 204, f'set-required fallo: {wa_req.status}'

        # 5) Sesion limpia para arrancar el login real desde cero.
        page.context.clear_cookies()
        yield page, email, admin
    finally:
        http.close()
        context.close()


def test_login_with_password_and_webauthn_required_lands_in_shell(
    mf_setup: tuple[Page, str, str],
) -> None:
    """
    Given un user con password Y passkey, ambos `required`,
    When inicia sesion completando los DOS factores en el checklist (password
        + passkey via Virtual Authenticator, en ese orden),
    Then el login converge (mfa_complete) y aterriza en el shell autenticado.

    Hoy FALLA: webauthn.login-verify no acumula los factores previos del
    checklist -> mfa_complete nunca true -> no hay redirect al shell.
    """
    page, email, admin = mf_setup

    # Act: login REAL por el form + checklist.
    page.goto(f'{admin}/login/', wait_until='load')
    page.get_by_test_id('login-email').fill(email)
    page.get_by_test_id('login-submit').click()
    page.wait_for_selector('[data-testid="login-checklist"]', timeout=20_000)

    # Factor 1: password.
    page.get_by_test_id('picker-method-password').click()
    page.get_by_test_id('checklist-password').fill(STRONG_PASSWORD)
    page.get_by_role('button', name='Continuar').click()
    page.wait_for_selector('text=1 de 2 completados', timeout=15_000)

    # Factor 2: webauthn (el Virtual Authenticator responde el ceremony).
    page.get_by_test_id('picker-method-webauthn').click()
    page.get_by_test_id('checklist-webauthn').click()

    # Assert: el login converge y aterriza en el shell.
    page.wait_for_selector(_SHELL_MARKER, timeout=30_000)
    assert page.url.rstrip('/') == admin
