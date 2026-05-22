"""@module shared.lambda_kit.error_codes — codigos de error comunes.

`ErrorCode` agrupa los codigos de error del estandar lambda-controller
por rango: 0 exito; 1xxx validacion; 2xxx configuracion; 4xxx negocio;
5xxx API/externo; 6xxx sistema.

Estos eran identicos (la base) en los 4 Lambdas del backend. Se
unificaron aca. Un Lambda que necesite codigos de dominio extra (ej.
`RATE_LIMIT_EXCEEDED`) los define como constantes propias en su
`settings/config.py` — el rango 4xxx queda reservado para eso.
"""

from __future__ import annotations

from enum import Enum


class ErrorCode(Enum):
    """Codigos de error internos, agrupados por rango.

    0 exito; 1xxx validacion; 2xxx configuracion; 4xxx negocio; 5xxx
    API/externo; 6xxx sistema. El handler colapsa el `code` del
    controller a un codigo de salida estable.
    """

    SUCCESS = 0

    # Validation errors (1000-1999)
    VALIDATION_ERROR = 1000
    VALIDATION_FIELD_REQUIRED = 1001
    VALIDATION_FIELD_INVALID = 1002

    # Configuration errors (2000-2999)
    CONFIGURATION_ERROR = 2000
    CONFIGURATION_MISSING = 2001

    # Business logic errors (4000-4999)
    BUSINESS_LOGIC_ERROR = 4000

    # External API errors (5000-5999)
    EXTERNAL_API_ERROR = 5000

    # System / unexpected errors (6000+)
    UNEXPECTED_ERROR = 6000
