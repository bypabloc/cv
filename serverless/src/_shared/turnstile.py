"""
Cloudflare Turnstile siteverify integration (modulo compartido).

Validacion de tokens Turnstile reutilizable por cualquier Lambda del backend
(hoy: contact_form). Centralizado en `_shared/` para que exista una sola
fuente de verdad — `_shared/` se incluye en el deploy zip de todas las
Lambdas, no requiere acoplamiento ni un Lambda Layer dedicado.

Decision: usar httpx (sincrono) con timeout 5s. Si falla -> raise TurnstileError.

API doc: https://developers.cloudflare.com/turnstile/get-started/server-side-validation/
Endpoint: POST challenges.cloudflare.com/turnstile/v0/siteverify
Form-encoded body: {secret, response, remoteip}
Response: {success: bool, hostname, error-codes, action, cdata, ...}
"""

from __future__ import annotations

import os
import re
from typing import Any

import httpx

from _shared.exceptions import TurnstileError
from _shared.logger import logger
from _shared.ssm_client import get_secret

TURNSTILE_SITEVERIFY_URL = (
    'https://challenges.cloudflare.com/turnstile/v0/siteverify'
)

# Hostnames siempre aceptados (compat con dev local). Subdominios *.localhost
# se aceptan solo en stage=dev via _LOCAL_SUBDOMAIN_PATTERN (RFC 6761 garantiza
# que resuelven a 127.0.0.1).
_BASE_HOSTNAMES = frozenset({'localhost', '127.0.0.1'})

# Pattern para subdominios *.localhost. Turnstile envia solo el hostname
# (sin scheme ni puerto), por eso no incluimos http:// ni :port aqui.
_LOCAL_SUBDOMAIN_PATTERN: re.Pattern[str] = re.compile(
    r'^[a-z0-9-]+\.localhost$',
)


def _expected_hostnames() -> frozenset[str]:
    """
    Hostnames validos del widget Turnstile para el stage actual.

    Se derivan de la env var CORS_ALLOWED_ORIGINS (la misma whitelist que
    usa cors.py, definida por stage en Mappings.StageConfig del SAM
    template): se extrae el host de cada origin `https://<host>`. Asi un
    solo lugar (`StageConfig`) define los hostnames del ambiente y no hay
    listas hardcodeadas que se desincronicen al cambiar de subdominio.
    """
    origins = os.environ.get('CORS_ALLOWED_ORIGINS', '').strip()
    hosts = set(_BASE_HOSTNAMES)
    for origin in origins.split(','):
        origin = origin.strip()
        if not origin:
            continue
        # `https://host` -> `host` (Turnstile reporta hostname sin scheme).
        host = origin.split('://', 1)[-1].split('/', 1)[0].split(':', 1)[0]
        if host:
            hosts.add(host)
    return frozenset(hosts)


def _hostname_allowed(hostname: str) -> bool:
    """True si hostname esta en whitelist del stage o es *.localhost en dev."""
    if hostname in _expected_hostnames():
        return True
    is_dev = os.environ.get('STAGE', 'dev') == 'dev'
    return is_dev and _LOCAL_SUBDOMAIN_PATTERN.match(hostname) is not None


_BYPASS_ALLOWED_STAGES = frozenset({'dev', 'local'})


def _load_bypass_secret() -> str:
    """
    Resuelve el bypass secret desde SSM. Solo se llama si STAGE in {dev,local}.

    Si el SSM_TURNSTILE_BYPASS_PATH no esta configurado o el param no existe,
    retorna string vacio (bypass queda inerte, regla #2).
    """
    bypass_path = os.environ.get('SSM_TURNSTILE_BYPASS_PATH', '')
    if not bypass_path:
        return ''
    try:
        return get_secret(bypass_path)
    except Exception:  # SSM ParameterNotFound, ClientError, etc.
        logger.info(
            'bypass secret not configured in SSM; bypass disabled',
            extra={'path': bypass_path},
        )
        return ''


def _try_bypass_turnstile(bypass_secret: str | None) -> dict[str, Any] | None:
    """
    Intenta usar el bypass de Turnstile para tests E2E.

    Reglas (defense-in-depth):
    1. SOLO se considera si `cf_response` viene vacio (caller llama esto antes
       de comparar con CF siteverify).
    2. SOLO se activa en STAGE in {dev, local}. En stage/prod retorna None.
    3. Requiere matchear el SSM param `/portfolio/dev/turnstile-bypass-secret`.
       El secret nunca llega al frontend (lo inyecta Playwright via
       page.addInitScript -> window.__playwright_turnstile_bypass).

    Returns:
        Dict con success=true si bypass aplica, `None` si no aplica
        (el caller debe seguir con el flujo normal de Turnstile).
    """
    stage = os.environ.get('STAGE', 'prod').lower()
    if stage not in _BYPASS_ALLOWED_STAGES:
        return None
    if not bypass_secret:
        return None
    expected_bypass = _load_bypass_secret()
    if not expected_bypass:
        return None
    if bypass_secret != expected_bypass:
        logger.warning(
            'turnstile bypass attempted with invalid secret',
            extra={'stage': stage},
        )
        return None
    logger.info('turnstile bypassed via secret header', extra={'stage': stage})
    return {'success': True, 'hostname': 'bypass', 'bypassed': True}


def verify_turnstile_token(
    cf_response: str,
    *,
    remote_ip: str | None = None,
    bypass_secret: str | None = None,
) -> dict[str, Any]:
    """
    Valida un Turnstile cf-response contra Cloudflare siteverify.

    Args:
        cf_response: valor del campo `cf-turnstile-response` del frontend.
            Si viene vacio se considera bypass para tests (regla #1).
        remote_ip: IP del cliente (opcional pero recomendado).
        bypass_secret: header X-Turnstile-Bypass-Secret. Solo se evalua si
            `cf_response` viene vacio Y STAGE esta en {dev, local}.

    Returns:
        Dict con la respuesta de siteverify si success=true.

    Raises:
        TurnstileError: si success=false, hostname inesperado, o timeout.
    """
    # Regla #1: bypass SOLO si cf_response viene vacio.
    # Astro nunca envia cf_response vacio (el form requiere el widget Turnstile),
    # asi que esta rama solo se activa desde tests automatizados.
    if not cf_response or not cf_response.strip():
        bypassed = _try_bypass_turnstile(bypass_secret)
        if bypassed is not None:
            return bypassed
        # Sin bypass valido y sin cf_response real -> CAPTCHA_INVALID
        msg = 'cf_token vacio y bypass no aplica'
        raise TurnstileError(msg, code='CAPTCHA_INVALID')

    secret_path = os.environ.get(
        'SSM_TURNSTILE_SECRET_PATH', '/portfolio/turnstile-secret'
    )
    secret = get_secret(secret_path)

    payload: dict[str, str] = {'secret': secret, 'response': cf_response}
    if remote_ip:
        payload['remoteip'] = remote_ip

    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.post(TURNSTILE_SITEVERIFY_URL, data=payload)
            response.raise_for_status()
            result: dict[str, Any] = response.json()
    except httpx.TimeoutException as e:
        msg = 'Turnstile siteverify timeout'
        raise TurnstileError(
            msg,
            code='CAPTCHA_TIMEOUT',
            extra={'remote_ip': remote_ip},
        ) from e
    except httpx.HTTPStatusError as e:
        msg = f'Turnstile siteverify HTTP {e.response.status_code}'
        raise TurnstileError(msg, code='CAPTCHA_HTTP_ERROR') from e
    except (httpx.HTTPError, ValueError) as e:
        msg = f'Turnstile siteverify failed: {e}'
        raise TurnstileError(msg, code='CAPTCHA_FAILED') from e

    if not result.get('success'):
        error_codes = result.get('error-codes', [])
        logger.warning(
            'turnstile verify failed',
            extra={
                'error_codes': error_codes,
                'remote_ip': remote_ip,
            },
        )
        msg = f'Turnstile verify failed: {error_codes}'
        raise TurnstileError(
            msg,
            code='CAPTCHA_INVALID',
            extra={'error_codes': error_codes},
        )

    # Validar hostname (defensa en profundidad contra widget hijacking).
    # En stage=dev se permite cualquier *.localhost (ver _hostname_allowed).
    hostname = result.get('hostname', '').lower()
    if hostname and not _hostname_allowed(hostname):
        logger.warning(
            'turnstile hostname mismatch',
            extra={'received_hostname': hostname, 'remote_ip': remote_ip},
        )
        msg = f'Hostname mismatch: {hostname!r}'
        raise TurnstileError(
            msg,
            code='CAPTCHA_HOSTNAME_MISMATCH',
            extra={'hostname': hostname},
        )

    return result
