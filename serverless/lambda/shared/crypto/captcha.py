"""Orquestador unico: CAPTCHA real de Turnstile o bypass firmado.

Punto de decision compartido por los Lambdas que protegen endpoints con
Turnstile (`contact_form`, `auth`). Reemplaza la logica de bypass que
antes vivia dentro de `shared.http.turnstile`: se movio aca para que ese
modulo quede httpx-puro y NO arrastre `cryptography` a sus otros
consumidores (cors, responses, validators -> los importan tracking_pixel
y cv, que NO deben vendorizar cryptography).

Reglas (defense-in-depth):
1. El bypass SOLO se considera si `cf_response` viene vacio (el frontend
   nunca lo envia vacio: el form exige el widget).
2. El bypass SOLO se activa en STAGE in {dev, local, stage}. En prod, un
   `cf_response` vacio -> CAPTCHA_INVALID directo (prod NUNCA acepta
   bypass). Cada env tiene su propio par de claves Ed25519 (aislamiento):
   un token firmado para dev NO sirve en stage (stage-binding del payload).
3. El bypass exige un token Ed25519 valido (firma con la clave PUBLICA del
   stage + no expirado + stage que coincide).

`time` se importa de stdlib (no es una dep externa, no rompe el contrato
shared-only). `cryptography` entra de forma lazy via
`shared.crypto.bypass_token` -> `shared.crypto.ed25519`.
"""

from __future__ import annotations

import os
import time
from typing import Any

from shared.core.exceptions import BypassTokenError, TurnstileError
from shared.observability.logger import logger

# Stages que aceptan el bypass de testing. prod NUNCA (defensa en
# profundidad). `local` es el modo offline-dev; `dev`/`stage` son los
# entornos desplegados de no-produccion.
_BYPASS_ALLOWED_STAGES = frozenset({'dev', 'local', 'stage'})


def _resolve_stage() -> str:
    """Stage actual del Lambda (default 'prod' = el mas restrictivo)."""
    return os.environ.get('STAGE', 'prod').lower()


def _load_public_key() -> str:
    """Resuelve la clave publica del bypass (cloud SSM o env var local).

    Catalogo: resources/secrets/turnstile-bypass-public-key.yaml. Cloud:
    devtools inyecta SSM_TURNSTILE_BYPASS_PUBLIC_KEY_PATH; local:
    TURNSTILE_BYPASS_PUBLIC_KEY. Si ninguna fuente la tiene, retorna ''
    (bypass inerte).
    """
    from shared.aws.ssm import get_parameter_by_name

    try:
        return get_parameter_by_name(
            'turnstile-bypass-public-key',
            local_env='TURNSTILE_BYPASS_PUBLIC_KEY',
        )
    except (RuntimeError, Exception):
        logger.info('bypass public key not configured; bypass disabled')
        return ''


def _try_bypass(bypass_token: str | None, stage: str) -> dict[str, Any] | None:
    """Intenta el bypass firmado. Devuelve dict success o None si no aplica.

    `None` significa "el bypass no aplica, segui con el flujo normal". Un
    token presente pero invalido NO devuelve None: levanta
    `TurnstileError(CAPTCHA_INVALID)` (el cliente no distingue bypass
    invalido de CAPTCHA real fallido).
    """
    if stage not in _BYPASS_ALLOWED_STAGES:
        return None
    if not bypass_token:
        return None
    public_key = _load_public_key()
    if not public_key:
        return None

    from shared.crypto.bypass_token import verify_bypass_token

    try:
        payload = verify_bypass_token(
            bypass_token,
            public_key_b64=public_key,
            stage=stage,
            now=int(time.time()),
        )
    except BypassTokenError as exc:
        # NUNCA loguear el token: solo el code y el jti si esta disponible.
        logger.warning(
            'bypass token rejected',
            extra={'stage': stage, 'reason': exc.code},
        )
        raise TurnstileError(
            'bypass token invalid',
            code='CAPTCHA_INVALID',
        ) from exc

    logger.info(
        'turnstile bypassed via signed token',
        extra={'stage': stage, 'jti': payload.get('jti')},
    )
    return {'success': True, 'hostname': 'bypass', 'bypassed': True}


def verify_captcha_or_bypass(
    cf_response: str,
    *,
    remote_ip: str | None = None,
    bypass_token: str | None = None,
    stage: str | None = None,
) -> dict[str, Any]:
    """Valida el CAPTCHA: Turnstile real si hay token CF, o bypass firmado.

    Args:
        cf_response: el `cf-turnstile-response` del frontend. Si viene
            vacio, se evalua el bypass (solo en dev/local).
        remote_ip: IP del cliente (para Cloudflare siteverify).
        bypass_token: header `X-Turnstile-Bypass-Token` (token Ed25519).
            Solo se evalua si `cf_response` viene vacio Y STAGE in
            {dev, local}.
        stage: override del stage (default: env STAGE). Util para tests.

    Returns:
        El dict de resultado (siteverify de Cloudflare, o el del bypass).

    Raises:
        TurnstileError: CAPTCHA_INVALID si el cf_response viene vacio y el
            bypass no aplica/falla; o los codes de siteverify si el token
            CF real falla.
    """
    if cf_response and cf_response.strip():
        # CAPTCHA real: import diferido para no acoplar el modulo a httpx
        # cuando solo se ejercita el path de bypass.
        from shared.http.turnstile import verify_turnstile_token

        return verify_turnstile_token(cf_response, remote_ip=remote_ip)

    effective_stage = (stage or _resolve_stage()).lower()
    bypassed = _try_bypass(bypass_token, effective_stage)
    if bypassed is not None:
        return bypassed

    raise TurnstileError(
        'cf_token vacio y bypass no aplica',
        code='CAPTCHA_INVALID',
    )
