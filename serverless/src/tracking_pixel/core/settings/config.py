"""Configuracion del Lambda `tracking_pixel`.

Define `AppConfig` (variables de entorno), los enums de codigos de error
y de metricas de logging, y reexporta el `logger` de la libreria comun.

El Lambda `tracking_pixel` usa el logger / tracer / metrics de Powertools
v3 que vive en `shared/` (vendorizado en `core/shared/` por devtools).
`config.py` reexporta el `logger` para que el resto del codigo `core/` lo
importe desde un solo lugar, como pide el estandar lambda-controller.

NOTA: este modulo NO usa `from __future__ import annotations`. `BaseSettings`
inspecciona `__annotations__` en runtime y compara `field_type is str`; con
anotaciones lazy (PEP 563) los tipos quedan como strings (`'str'`) y la
carga de env vars no detectaria los campos. Las anotaciones deben ser los
tipos reales.
"""

from enum import Enum

from utils.base_settings import BaseSettings

from shared.observability.logger import logger

__all__ = ['AppConfig', 'ErrorCode', 'LogMetricType', 'app_config', 'logger']


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
    RATE_LIMITED = 4001

    # External API errors (5000-5999)
    EXTERNAL_API_ERROR = 5000

    # System / unexpected errors (6000+)
    UNEXPECTED_ERROR = 6000


class LogMetricType(Enum):
    """Tipos de metrica para logging estructurado.

    Cada log estructurado lleva un `metric_type` en su `extra`, lo que
    permite construir metricas y filtros en CloudWatch.
    """

    # Lambda lifecycle
    LAMBDA_START = 'LAMBDA_START'
    LAMBDA_SUCCESS = 'LAMBDA_SUCCESS'
    LAMBDA_UNEXPECTED_ERROR = 'LAMBDA_UNEXPECTED_ERROR'

    # Phase lifecycle
    PHASE_START = 'PHASE_START'
    PHASE_COMPLETE = 'PHASE_COMPLETE'

    # Event validation
    EVENT_VALIDATION_FAILED = 'EVENT_VALIDATION_FAILED'
    EVENT_VALIDATION_PYDANTIC_ERROR = 'EVENT_VALIDATION_PYDANTIC_ERROR'
    EVENT_VALIDATION_UNEXPECTED_ERROR = 'EVENT_VALIDATION_UNEXPECTED_ERROR'

    # Controller lifecycle
    CONTROLLER_NOT_FOUND = 'CONTROLLER_NOT_FOUND'
    CONTROLLER_EXECUTE_START = 'CONTROLLER_EXECUTE_START'
    CONTROLLER_SUCCESS = 'CONTROLLER_SUCCESS'
    CONTROLLER_ERROR = 'CONTROLLER_ERROR'

    # Phase failures
    PRELOAD_PHASE_FAILED = 'PRELOAD_PHASE_FAILED'
    VALIDATE_PHASE_FAILED = 'VALIDATE_PHASE_FAILED'
    EXECUTE_PHASE_FAILED = 'EXECUTE_PHASE_FAILED'

    # Import controller
    INVALID_OPERATION = 'INVALID_OPERATION'
    CONTROLLER_IMPORT_ERROR = 'CONTROLLER_IMPORT_ERROR'
    CONTROLLER_CLASS_NOT_FOUND = 'CONTROLLER_CLASS_NOT_FOUND'

    # Tracking operations (dominio del Lambda tracking_pixel)
    TRACKING_EVENT_RECEIVED = 'TRACKING_EVENT_RECEIVED'
    TRACKING_EVENT_PERSISTED = 'TRACKING_EVENT_PERSISTED'
    TRACKING_EVENT_REJECTED = 'TRACKING_EVENT_REJECTED'


class AppConfig(BaseSettings):
    """Configuracion del Lambda `tracking_pixel`, desde env vars.

    Cada campo anotado se carga de la env var homonima en MAYUSCULAS.
    Los valores de tabla los inyecta el template SAM (ver lambda.yaml).
    """

    environment: str = 'dev'

    # Nombre de la tabla DynamoDB de tracking (TTL 60d). La capa de
    # persistence la lee; se centraliza aqui para no dispersar os.environ.
    tracking_table_name: str = 'portfolio-tracking-dev'

    # Testing
    testing: str = '0'

    def is_testing(self) -> bool:
        """Devuelve True si el servicio corre en modo testing."""
        return self.testing == '1'


# Singleton de configuracion: se evalua una vez en el cold start.
app_config = AppConfig()
