"""
SSM Parameter Store helpers con Powertools Parameters cache.

Wraps `aws_lambda_powertools.utilities.parameters.get_parameter` para:
- Cache nativo Powertools (per Lambda warm cycle, default 5 min)
- Manejo de SecureString con KMS decrypt automatico
- API uniforme `get_secret(path)` para todo el codebase

Decision (.claude/docs/aws-lambda/04-cold-start-optimization.md):
Cache reduce SSM GetParameter calls de N por invocacion a 1 cada 5 min.
A $0.05/10K calls + ~30ms latencia, el cache ahorra ambos.

Uso:
    from shared.aws.ssm import get_secret, get_parameter

    secret = get_secret('/portfolio/turnstile-secret')  # SecureString
    email = get_parameter('/portfolio/owner-email')      # String
"""

from __future__ import annotations

import os
from typing import Any

from aws_lambda_powertools.utilities import parameters

# TTL del cache Powertools en segundos
_CACHE_TTL = int(os.environ.get('SSM_CACHE_SECONDS', '300'))


def get_secret(path: str, *, max_age: int | None = None) -> str:
    """
    Lee un SSM SecureString con KMS decrypt + cache.

    Args:
        path: path del parameter (ej: '/portfolio/turnstile-secret').
        max_age: TTL del cache en segundos (default: SSM_CACHE_SECONDS env).

    Returns:
        El valor decrypted del SecureString.

    Raises:
        parameters.GetParameterError: si SSM falla o el path no existe.
    """
    ttl = max_age if max_age is not None else _CACHE_TTL
    value = parameters.get_parameter(path, decrypt=True, max_age=ttl)
    if not isinstance(value, str):
        msg = f'SSM path {path!r} returned non-string'
        raise TypeError(msg)
    return value


def get_parameter(path: str, *, max_age: int | None = None) -> str:
    """
    Lee un SSM String (no encrypted) con cache.

    Args:
        path: path del parameter (ej: '/portfolio/owner-email').
        max_age: TTL del cache en segundos.

    Returns:
        El valor del String.
    """
    ttl = max_age if max_age is not None else _CACHE_TTL
    value = parameters.get_parameter(path, max_age=ttl)
    if not isinstance(value, str):
        msg = f'SSM path {path!r} returned non-string'
        raise TypeError(msg)
    return value


def clear_cache() -> None:
    """Limpia el cache Powertools (usado en tests)."""
    # Powertools parameters cache es interno; limpiarlo via private API
    # solo es seguro en tests, no en runtime.
    cache: Any = getattr(parameters, '_DEFAULT_PROVIDERS', None)
    if cache is not None:
        cache.clear()


def _short_name_to_upper(short_name: str) -> str:
    """Convierte un short_name del catalogo a UPPER_UNDER.

    Convencion: 'turnstile-secret' -> 'TURNSTILE_SECRET'.
    """
    return short_name.upper().replace('-', '_')


def get_secret_by_name(
    short_name: str,
    *,
    local_env: str | None = None,
) -> str:
    """Resuelve un secreto del catalogo (cloud SSM o local env var).

    devtools inyecta dos env vars al Lambda segun el modo:
      - cloud: SSM_<UPPER>_PATH = path SSM (el helper hace SSM lookup)
      - local: <local_env> = valor directo del .env

    Si `local_env` no se provee, busca tambien `SECRET_<UPPER>` por
    convencion.

    Args:
        short_name: nombre corto del catalogo
            (ej: 'turnstile-secret', 'neon-url').
        local_env: env var del valor directo en modo local
            (ej: 'TURNSTILE_SECRET_KEY', 'DB_URL').

    Returns:
        El valor del secreto.

    Raises:
        RuntimeError: si ninguna fuente tiene el valor.
    """
    upper = _short_name_to_upper(short_name)
    ssm_path_env = f'SSM_{upper}_PATH'
    ssm_path = os.environ.get(ssm_path_env)
    if ssm_path:
        return get_secret(ssm_path)
    # Local mode
    if local_env:
        direct = os.environ.get(local_env)
        if direct:
            return direct
    fallback = os.environ.get(f'SECRET_{upper}')
    if fallback:
        return fallback
    candidates = [ssm_path_env]
    if local_env:
        candidates.append(local_env)
    candidates.append(f'SECRET_{upper}')
    raise RuntimeError(
        f'No se puede resolver el secreto {short_name!r}: ninguna de '
        f'estas env vars esta seteada: {candidates}',
    )


def get_parameter_by_name(
    short_name: str,
    *,
    local_env: str | None = None,
) -> str:
    """Resuelve un parametro NO-secreto del catalogo (cloud SSM o env var).

    Variante de `get_secret_by_name` para parametros `String` planos (sin
    KMS): usa `get_parameter` (sin decrypt) en vez de `get_secret`. Mismo
    patron de resolucion cloud/local:
      - cloud: SSM_<UPPER>_PATH = path SSM (lookup con get_parameter)
      - local: <local_env> = valor directo del .env

    Pensado para valores publicos como la clave PUBLICA del bypass de
    Turnstile (`turnstile-bypass-public-key`): no es secreta, no requiere
    KMS, y pedir decrypt sobre un String plano seria semanticamente
    incorrecto.

    Args:
        short_name: nombre corto del catalogo
            (ej: 'turnstile-bypass-public-key').
        local_env: env var del valor directo en modo local
            (ej: 'TURNSTILE_BYPASS_PUBLIC_KEY').

    Returns:
        El valor del parametro.

    Raises:
        RuntimeError: si ninguna fuente tiene el valor.
    """
    upper = _short_name_to_upper(short_name)
    ssm_path_env = f'SSM_{upper}_PATH'
    ssm_path = os.environ.get(ssm_path_env)
    if ssm_path:
        return get_parameter(ssm_path)
    if local_env:
        direct = os.environ.get(local_env)
        if direct:
            return direct
    candidates = [ssm_path_env]
    if local_env:
        candidates.append(local_env)
    raise RuntimeError(
        f'No se puede resolver el parametro {short_name!r}: ninguna de '
        f'estas env vars esta seteada: {candidates}',
    )
