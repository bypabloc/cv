"""
Cloudflare Turnstile siteverify integration (modulo compartido).

Validacion de tokens Turnstile reutilizable por cualquier Lambda del backend
(hoy: contact_form). Centralizado en `shared/` para que exista una sola
fuente de verdad — `shared/` se incluye en el deploy zip de todas las
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

from shared.core.exceptions import TurnstileError
from shared.observability.logger import logger

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


def verify_turnstile_token(
    cf_response: str,
    *,
    remote_ip: str | None = None,
) -> dict[str, Any]:
    """
    Valida un Turnstile cf-response contra Cloudflare siteverify.

    httpx-puro: este modulo NO conoce el bypass de testing. El bypass
    firmado (Ed25519) vive en `shared.crypto.captcha.verify_captcha_or_bypass`,
    que delega a esta funcion SOLO cuando hay un `cf_response` real. Asi
    `shared.http` no arrastra `cryptography` a sus consumidores
    (tracking_pixel, cv).

    Args:
        cf_response: valor del campo `cf-turnstile-response` del frontend.
            DEBE venir no-vacio: el caller (orquestador) ya separo el path
            de bypass. Un `cf_response` vacio aca -> CAPTCHA_INVALID.
        remote_ip: IP del cliente (opcional pero recomendado).

    Returns:
        Dict con la respuesta de siteverify si success=true.

    Raises:
        TurnstileError: si cf_response vacio, success=false, hostname
            inesperado, o timeout.
    """
    if not cf_response or not cf_response.strip():
        # El bypass ya no vive aca: un cf_response vacio es siempre invalido.
        msg = 'cf_token vacio'
        raise TurnstileError(msg, code='CAPTCHA_INVALID')

    # Catalogo: serverless/lambda/resources/secrets/turnstile-secret.yaml.
    # Cloud: devtools inyecta SSM_TURNSTILE_SECRET_PATH; local: TURNSTILE_SECRET_KEY.
    from shared.aws.ssm import get_secret_by_name

    secret = get_secret_by_name(
        'turnstile-secret', local_env='TURNSTILE_SECRET_KEY',
    )

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
    # `or ''` cubre el caso en que siteverify devuelve `"hostname": null`
    # (key presente pero null): .get(key, '') retorna None, no el default,
    # y None.lower() crashearia toda la validacion.
    hostname = (result.get('hostname') or '').lower()
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
