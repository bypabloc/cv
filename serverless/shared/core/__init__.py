"""
Subpaquete `core`: primitivos compartidos sin dependencias de dominio.

Agrupa la configuracion (env vars), la jerarquia de excepciones, los
TypedDicts del evento Lambda y el generador de UUIDv7. Es la base del
arbol de `shared/`: el resto de subpaquetes puede importar de aca, pero
`core` no importa de ningun otro subpaquete de `shared`.

Convencion: importar SIEMPRE desde `shared.core.<modulo>`.
"""

from shared.core.config import Settings, get_settings, settings
from shared.core.exceptions import (
    ApplicationError,
    CountryBlockedError,
    IPBlacklistedError,
    RateLimitExceededError,
    TurnstileError,
    ValidationError,
)
from shared.core.types import (
    ErrorPayload,
    JsonResponse,
    LambdaEvent,
    RequestContext,
    RequestContextIdentity,
)
from shared.core.ulid import new_uuidv7

__all__ = [
    'ApplicationError',
    'CountryBlockedError',
    'ErrorPayload',
    'IPBlacklistedError',
    'JsonResponse',
    'LambdaEvent',
    'RateLimitExceededError',
    'RequestContext',
    'RequestContextIdentity',
    'Settings',
    'TurnstileError',
    'ValidationError',
    'get_settings',
    'new_uuidv7',
    'settings',
]
