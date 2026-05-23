"""
Subpaquete `core`: primitivos compartidos sin dependencias de dominio.

Agrupa la configuracion (env vars), la jerarquia de excepciones, los
TypedDicts del evento Lambda y el generador de UUIDv7. Es la base del
arbol de `shared/`: el resto de subpaquetes puede importar de aca, pero
`core` no importa de ningun otro subpaquete de `shared`.

Tambien actua como portador unico de pydantic: re-exporta `BaseModel`,
`Field`, `EmailStr`, `field_validator`, `model_validator` y `ConfigDict`
para que los `core/` de los services NO importen `from pydantic` directo
(ver `.claude/rules/lambda-shared-imports.md`).

Convencion: importar SIEMPRE desde `shared.core` o `shared.core.<modulo>`.
"""

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)
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
    'BaseModel',
    'ConfigDict',
    'CountryBlockedError',
    'EmailStr',
    'ErrorPayload',
    'Field',
    'IPBlacklistedError',
    'JsonResponse',
    'LambdaEvent',
    'RateLimitExceededError',
    'RequestContext',
    'RequestContextIdentity',
    'Settings',
    'TurnstileError',
    'ValidationError',
    'field_validator',
    'get_settings',
    'model_validator',
    'new_uuidv7',
    'settings',
]
