"""
CORS helpers para los 6 subdominios del portfolio.

Decision: NO usar `Access-Control-Allow-Origin: *` porque el form de
contacto y el tracking pixel pueden necesitar `credentials: include` en
el futuro (para auth basic del dashboard). Mejor whitelist explicita +
echo del Origin header matcheado.

Whitelist: 6 subdominios bajo the-full-stack.com (apex + 5 niches).
"""

from __future__ import annotations

import os
import re
from typing import Final

# Origins permitidos. Sobrescribible via env var CORS_ALLOWED_ORIGINS
# (CSV) cuando se quiera agregar dominios extra (ej: staging).
_DEFAULT_WHITELIST: Final[tuple[str, ...]] = (
    'https://the-full-stack.com',
    'https://hub.the-full-stack.com',
    'https://fintech.the-full-stack.com',
    'https://architect.the-full-stack.com',
    'https://leader.the-full-stack.com',
    'https://vibe.the-full-stack.com',
)

# Localhost apex para dev local (Docker stack ports 9970-9973 + Astro dev 4321).
# Los subdominios (hub.localhost, architect.localhost, etc.) se matchean por
# pattern aparte (ver _LOCAL_SUBDOMAIN_PATTERN). RFC 6761 garantiza que
# *.localhost siempre resuelve a 127.0.0.1, por lo que cualquier subdomain
# en stage dev es seguro.
_LOCAL_WHITELIST: Final[tuple[str, ...]] = (
    'http://localhost:9970',
    'http://localhost:9971',
    'http://localhost:9972',
    'http://localhost:9973',
    'http://localhost:4321',
)

# Pattern para subdominios localhost: http://<word>.localhost:<port>.
# Solo aplica en stage=dev (ver is_allowed_origin).
_LOCAL_SUBDOMAIN_PATTERN: Final[re.Pattern[str]] = re.compile(
    r'^http://[a-z0-9-]+\.localhost(:\d+)?$',
)


def _load_whitelist() -> tuple[str, ...]:
    """Carga whitelist desde env var o usa el default + localhost si stage=dev."""
    custom = os.environ.get('CORS_ALLOWED_ORIGINS', '').strip()
    if custom:
        return tuple(s.strip() for s in custom.split(',') if s.strip())

    base = _DEFAULT_WHITELIST
    if os.environ.get('STAGE', 'dev') == 'dev':
        base = base + _LOCAL_WHITELIST
    return base


def is_allowed_origin(origin: str | None) -> bool:
    """
    True si el origin esta en la whitelist.

    En stage=dev, ademas acepta cualquier `http://<subdomain>.localhost[:port]`
    via pattern (RFC 6761 garantiza que *.localhost resuelve a 127.0.0.1, asi
    que es seguro permitir subdominios arbitrarios localmente).

    Examples:
        >>> import os
        >>> os.environ.pop('CORS_ALLOWED_ORIGINS', None)
        >>> os.environ['STAGE'] = 'prod'
        >>> is_allowed_origin('https://the-full-stack.com')
        True
        >>> is_allowed_origin('https://evil.com')
        False
        >>> is_allowed_origin(None)
        False
        >>> os.environ['STAGE'] = 'dev'
        >>> is_allowed_origin('http://architect.localhost:9970')
        True
        >>> is_allowed_origin('http://hub.localhost:9970')
        True
        >>> os.environ['STAGE'] = 'prod'
        >>> is_allowed_origin('http://architect.localhost:9970')
        False
    """
    if not origin:
        return False
    if origin in _load_whitelist():
        return True
    # En dev permitimos cualquier subdominio *.localhost (RFC 6761 seguro)
    return bool(
        os.environ.get('STAGE', 'dev') == 'dev'
        and _LOCAL_SUBDOMAIN_PATTERN.match(origin)
    )


def resolve_origin(headers: dict[str, str] | None) -> str:
    """
    Echo del Origin header SI esta en whitelist, sino el primer origin
    default (the-full-stack.com).

    Usado en respuestas exitosas: si el browser hizo la request desde
    `https://hub.the-full-stack.com`, le devolvemos ese mismo origin en
    `Access-Control-Allow-Origin` (no devolver * para no romper futuro
    credentials: include).
    """
    if not headers:
        return _DEFAULT_WHITELIST[0]

    # Lookup case-insensitive
    origin: str | None = None
    for key, value in headers.items():
        if key.lower() == 'origin':
            origin = value
            break

    if origin and is_allowed_origin(origin):
        return origin

    # Fallback: primer origin default (apex)
    return _DEFAULT_WHITELIST[0]


def public_cors_origin() -> str:
    """
    Origin para endpoints publicos sin credenciales: siempre `'*'`.

    `navigator.sendBeacon` (modo `ping`) — usado por el tracking pixel —
    exige `Access-Control-Allow-Origin: *` literal en la respuesta. Un echo
    del Origin (aunque este en whitelist) hace fallar la request `ping` con
    CORS error. El endpoint `/track` es tracking anonimo: NUNCA usa cookies
    ni `credentials: include`, asi que `'*'` es correcto y seguro.

    NO usar en `/contact`: ese endpoint hace `fetch` normal y podria
    necesitar credentials a futuro — ahi va `resolve_origin()` (echo).

    Examples:
        >>> public_cors_origin()
        '*'
    """
    return '*'


def cors_headers(origin: str) -> dict[str, str]:
    """
    Build headers CORS para una respuesta JSON.

    Args:
        origin: el origin a echo en Access-Control-Allow-Origin. Puede ser
                un origin concreto (echo via `resolve_origin()`) o `'*'`
                (endpoints publicos via `public_cors_origin()`).

    Returns:
        Dict con los headers CORS. `Vary: Origin` se incluye SOLO cuando el
        origin es un echo concreto — la respuesta varia segun el Origin. Con
        `'*'` la respuesta NO varia, y mandar `Vary: Origin` junto a `'*'`
        es contradictorio: `navigator.sendBeacon` (modo `ping`) rechaza esa
        combinacion con CORS error. Por eso con `'*'` se omite el `Vary`.
    """
    headers = {
        'Access-Control-Allow-Origin': origin,
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
        # Authorization: el admin manda `Authorization: Bearer <JWT>` en los
        # endpoints autenticados (/users completo, /auth mfa/webauthn con
        # sesion). Sin este header en el allow-list, el browser bloquea el
        # request con error CORS. Debe coincidir con el allowed_headers del
        # MOCK del OPTIONS en devtools/serverless/provisioner.py.
        'Access-Control-Allow-Headers': (
            'Content-Type,Authorization,X-Turnstile-Token,X-Turnstile-Bypass-Token'
        ),
        'Access-Control-Max-Age': '600',
    }
    if origin != '*':
        headers['Vary'] = 'Origin'
    return headers
