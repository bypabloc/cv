"""Configuracion del harness api_e2e: URLs, origins, pool de IPs.

Una sola fuente para los endpoints por entorno de deploy y los helpers de
datos sinteticos (emails del SES simulator, IPs de documentacion).
"""

from __future__ import annotations

import secrets as _secrets


# Entornos de DEPLOY soportados (NUNCA prod: el harness muta el entorno).
VALID_ENVS = ('dev', 'stage')

# Region de los recursos AWS (SSM, Lambda) del backend.
AWS_REGION = 'us-east-1'

_API_BASE = {
    'dev': 'https://api.portfolio.dev.the-full-stack.com',
    'stage': 'https://api.portfolio.stage.the-full-stack.com',
}

_ADMIN_ORIGIN = {
    'dev': 'https://admin.portfolio.dev.the-full-stack.com',
    'stage': 'https://admin.portfolio.stage.the-full-stack.com',
}
_CV_ORIGIN = {
    'dev': 'https://fintech.portfolio.dev.the-full-stack.com',
    'stage': 'https://fintech.portfolio.stage.the-full-stack.com',
}
_APEX_ORIGIN = {
    'dev': 'https://the-full-stack.com',
    'stage': 'https://the-full-stack.com',
}

_BYPASS_SSM = {
    'dev': '/portfolio/dev/turnstile-bypass-secret',
    'stage': '/portfolio/stage/turnstile-bypass-secret',
}

_NEON_SSM = {
    'dev': '/portfolio/dev/neon-url',
    'stage': '/portfolio/stage/neon-url',
}

# UUID de un event_type valido (catalogo taxonomy) para tracking.
TRACKING_EVENT_TYPE_ID = '019e372b-e0a7-7154-8279-8829bcf6a08c'

# Niche valido para cv/tracking.
NICHE = 'fintech'


def api_base(env: str) -> str:
    """Base URL del API Gateway para el entorno de deploy."""
    return _API_BASE[env]


def admin_origin(env: str) -> str:
    """Origin del dashboard (auth/users) para el entorno."""
    return _ADMIN_ORIGIN[env]


def cv_origin(env: str) -> str:
    """Origin de un niche (cv) para el entorno."""
    return _CV_ORIGIN[env]


def apex_origin(env: str) -> str:
    """Origin del apex (contact/tracking) para el entorno."""
    return _APEX_ORIGIN[env]


def bypass_ssm_path(env: str) -> str:
    """SSM path del bypass secret de Turnstile."""
    return _BYPASS_SSM[env]


def neon_ssm_path(env: str) -> str:
    """SSM path de la connection string de Neon."""
    return _NEON_SSM[env]


def turnstile_bypass_supported(env: str) -> bool:
    """True si el entorno evalua el header X-Turnstile-Bypass-Secret.

    Solo `dev` (y `local`) lo evaluan; en `stage` el bypass es inerte
    (shared.http.turnstile._BYPASS_ALLOWED_STAGES), asi que los flujos
    que dependen del bypass se omiten en stage.
    """
    return env == 'dev'


# Pool de IPs de documentacion (TEST-NET RFC 5737): 1 IP unica por request
# para no agotar el rate-limit ni auto-blacklistear una IP real.
_IP_POOL: list[str] = [
    f'{net}.{host}'
    for net in ('198.51.100', '203.0.113', '192.0.2')
    for host in range(1, 255)
]


class IpRotator:
    """Entrega una IP distinta por llamada (round-robin sobre TEST-NET)."""

    def __init__(self) -> None:
        self._idx = 0

    def next(self) -> str:
        """Siguiente IP del pool (cicla)."""
        ip = _IP_POOL[self._idx % len(_IP_POOL)]
        self._idx += 1
        return ip


# Marca para identificar (y limpiar) todo lo creado por el harness.
RUN_TAG = 'api-e2e'


def synthetic_email(run_id: str, slot: str) -> str:
    """Email sintetico unico via el SES mailbox simulator.

    `success+<tag>@simulator.amazonses.com`: globalmente entregable (pasa
    el EmailStr de pydantic) y el worker "envia" sin entrega real. El tag
    embebe el RUN_TAG + run_id + slot para unicidad y trazabilidad.
    """
    suffix = _secrets.token_hex(3)
    return (
        f'success+{RUN_TAG}-{run_id}-{slot}-{suffix}'
        '@simulator.amazonses.com'
    )
