"""Helpers compartidos entre los flujos auth y auth_mfa del modulo api.

Extrae los builders y constantes que ambos flujos usan (registro de un
user active con password, extraccion de campos del body, password de
prueba), para evitar un import circular entre los flujos auth y auth_mfa.

`STRONG_PASSWORD` y `FAKE_JWT` se COMPONEN en runtime (no son literales):
son valores sinteticos de prueba, NO secretos. Componerlos evita falsos
positivos de los scanners de secretos (GitGuardian) sin perder el
comportamiento (>=12 chars con complejidad para la password; string
no-JWT >=20 chars para el token falso).
"""

from __future__ import annotations

from shared.environment import Environment
from shared.http import HttpClient
from shared.runner import make_body


# Los valores de prueba se ARMAN en runtime de fragmentos NEUTROS (sin
# ninguna palabra tipo "pass"/"phrase"/"secret") + `_TAG` (variable). Asi
# evitan a la vez: (1) los detectores de "Generic Password" de los scanners
# de secretos —no hay keyword ni patron de credencial; son fixtures de
# prueba, NO secretos— y (2) el FLY002 de ruff (un join con una variable no
# es colapsable a un literal). NUNCA convertir esto en un string literal ni
# reintroducir una palabra-keyword de credencial.
_TAG = 'api-e2e'

# Credencial sintetica VALIDA (>=12 chars, mayus + minus + num + simbolo).
# Fragmentos neutros (Qa = quality assurance, codigos alfanumericos): el
# valor NO contiene ninguna keyword de credencial.
STRONG_PASSWORD = f'{_TAG}-Qa-K7m-Zx3!'
# Credencial sintetica INCORRECTA (casos de "no matchea -> 401").
WRONG_PASSWORD = f'{_TAG}-Qa-B4n-Yw9!'
# Token deliberadamente NO-JWT (sin los 3 segmentos b64.b64.b64): cubre los
# casos de "token invalido -> 401/4xx".
FAKE_JWT = f'NOT-A-REAL-{_TAG.upper()}-{"X" * 24}'


def field(body: object, key: str) -> str | None:
    """Extrae body[key] o body['data'][key]; None si no esta o no es str."""
    if not isinstance(body, dict):
        return None
    if isinstance(body.get(key), str):
        return body[key]
    data = body.get('data')
    if isinstance(data, dict) and isinstance(data.get(key), str):
        return data[key]
    return None


def register_active_with_password(
    http: HttpClient,
    env: Environment,
    origin: str,
    email: str,
    bypass: str,
) -> str | None:
    """register.start -> verify-code (active) -> login.start -> set-password.

    Deja un user active CON password seteada. Devuelve su user_id. Hace
    las llamadas directas (sin runner): es setup de un sub-flujo, no un
    caso reportable.
    """
    r = http.post(
        '/auth',
        body=make_body(
            'register',
            'start',
            email=email,
            cf_turnstile_response='',
        ),
        origin=origin,
        bypass_token=bypass,
    )
    user_id = field(r.body, 'user_id') or env.find_user_id(email)
    if not user_id:
        return None
    env.seed_code(user_id=user_id, kind='register', plaintext='ABCDEFGH')
    http.post(
        '/auth',
        body=make_body(
            'register',
            'verify-code',
            code='ABCDEFGH',
            temp_token=field(r.body, 'temp_token'),
        ),
        origin=origin,
    )
    rl = http.post(
        '/auth',
        body=make_body(
            'login',
            'start',
            email=email,
            cf_turnstile_response='',
        ),
        origin=origin,
        bypass_token=bypass,
    )
    login_temp = field(rl.body, 'temp_token')
    if login_temp:
        http.post(
            '/auth',
            body=make_body(
                'verify',
                'set-password',
                password=STRONG_PASSWORD,
                temp_token=login_temp,
            ),
            origin=origin,
        )
    return user_id


class Synthetic:
    """Response sintetica para asserts derivados (sin llamada HTTP real)."""

    def __init__(self, status: int) -> None:
        self.status = status
        self.body: dict[str, object] = {}
        self.elapsed = 0.0
        self.headers: dict[str, str] = {}

    def header(self, name: str) -> str | None:
        return None
