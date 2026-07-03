"""Configuracion del harness E2E: URLs, origins, pool de IPs.

Una sola fuente para los endpoints por entorno de deploy y los helpers de
datos sinteticos (emails del SES simulator, IPs de documentacion). Incluye
el mapa de los 6 niches DESPLEGADOS para el modulo `app` (browser).
"""

from __future__ import annotations

import secrets as _secrets


# Entornos de DEPLOY soportados (NUNCA prod: el harness muta el entorno).
VALID_ENVS = ('dev',)

# Region de los recursos AWS (SSM, Lambda) del backend.
AWS_REGION = 'us-east-1'

_API_BASE = {
    'dev': 'https://api.portfolio.dev.the-full-stack.com',
}

_ADMIN_ORIGIN = {
    'dev': 'https://admin.portfolio.dev.the-full-stack.com',
}
_CV_ORIGIN = {
    'dev': 'https://fintech.portfolio.dev.the-full-stack.com',
}
_APEX_ORIGIN = {
    'dev': 'https://the-full-stack.com',
}

_NEON_SSM = {
    'dev': '/portfolio/dev/neon-url',
}

# UUID de un event_type valido (catalogo taxonomy) para tracking.
TRACKING_EVENT_TYPE_ID = '019e372b-e0a7-7154-8279-8829bcf6a08c'

# Niche valido para cv/tracking.
NICHE = 'fintech'

# Sitios DESPLEGADOS (cada uno es un Cloudflare Pages project propio).
# `generic` NO esta aqui: es el apex (ver _NICHE_ORIGIN + niche_origin).
# `journey` no es un niche del CV pero cuelga del subdominio igual.
NICHES = ('hub', 'fintech', 'architect', 'leader', 'vibe', 'journey')

# Origins de los 6 niches DESPLEGADOS por env, para el modulo `app`.
# Patron de los niches:  {niche}.portfolio.{env}.the-full-stack.com
# `generic` = apex: en dev NO tiene apex propio (apex_domain=None en
#   cloudflare_setup/config.py), asi que usa el base_domain del env
#   (portfolio.{env}.the-full-stack.com). En prod seria the-full-stack.com,
#   pero el harness NUNCA corre contra prod (VALID_ENVS = dev).
_NICHE_ORIGIN = {
    'dev': {
        **{
            n: f'https://{n}.portfolio.dev.the-full-stack.com'
            for n in NICHES
        },
        'generic': 'https://portfolio.dev.the-full-stack.com',
    },
}


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


def niche_origin(niche: str, env: str) -> str:
    """Origin desplegado de un niche (o `generic`/apex) para el entorno.

    `generic` resuelve al apex del env (en dev: el base_domain
    `portfolio.{env}.the-full-stack.com`, porque esos envs no tienen apex
    propio). El resto de niches sigue
    `{niche}.portfolio.{env}.the-full-stack.com`.
    """
    return _NICHE_ORIGIN[env][niche]


def neon_ssm_path(env: str) -> str:
    """SSM path de la connection string de Neon."""
    return _NEON_SSM[env]


def turnstile_bypass_supported(env: str) -> bool:
    """True si el entorno evalua el header X-Turnstile-Bypass-Token.

    `dev` y `stage` lo evaluan (shared.crypto.captcha._BYPASS_ALLOWED_STAGES
    = {dev, local, stage}); prod NUNCA. El harness solo corre contra dev y
    stage, asi que el bypass aplica a ambos.
    """
    return env in ('dev',)


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
    return f'success+{RUN_TAG}-{run_id}-{slot}-{suffix}@simulator.amazonses.com'
