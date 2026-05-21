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
    from shared.ssm_client import get_secret, get_parameter

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
