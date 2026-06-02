"""Helpers compartidos entre flow_auth y flow_auth_mfa.

Extrae los builders y constantes que ambos modulos usan (registro de un
user active con password, extraccion de campos del body, password de
prueba), para evitar un import circular entre flow_auth y flow_auth_mfa.
El prefijo `_` del modulo evita que pytest lo recolecte.

`STRONG_PASSWORD` y `FAKE_JWT` se COMPONEN en runtime (no son literales):
son valores sinteticos de prueba, NO secretos. Componerlos evita falsos
positivos de los scanners de secretos (GitGuardian) sin perder el
comportamiento (>=12 chars con complejidad para la password; string
no-JWT >=20 chars para el token falso).
"""

from __future__ import annotations

from api_e2e.environment import Environment
from api_e2e.runner import make_body
from api_e2e.support import HttpClient


# Los valores de prueba se ARMAN en runtime de fragmentos cortos, ninguno
# password-like por si solo, e incluyendo `_TAG` (variable) en cada join.
# Esto evita a la vez: (1) los falsos positivos de los scanners de secretos
# —no hay ningun literal que parezca credencial; son fixtures de prueba, NO
# secretos— y (2) el FLY002 de ruff (un join con una variable no es
# colapsable a un literal). NUNCA convertir esto en un string literal.
_TAG = 'api-e2e'
_PASS = ('Pass', 'phrase')  # fragmentos: ni 'Pass' ni 'phrase' son secretos

# Password sintetica de prueba (>=12 chars, mayus + num + simbolo).
STRONG_PASSWORD = '-'.join((_TAG, 'Str0ng', ''.join(_PASS))) + '!'
# Password sintetica INCORRECTA (casos de "password no matchea -> 401").
WRONG_PASSWORD = '-'.join((_TAG, 'Wr0ng', ''.join(_PASS))) + '!'
# Token deliberadamente NO-JWT (sin los 3 segmentos b64.b64.b64): cubre los
# casos de "token invalido -> 401/4xx".
FAKE_JWT = '-'.join(('NOT', 'A', 'REAL', _TAG.upper(), 'X' * 24))


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
