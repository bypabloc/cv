"""Configuracion del Lambda `tracking_worker`.

Define `AppConfig` (variables de entorno), los enums de codigos de
error y de metricas de logging, y reexporta el `logger` de la libreria
comun.

El Lambda usa el logger / tracer / metrics de Powertools v3 que vive
en `shared/` (vendorizado en `core/shared/` por devtools). `config.py`
reexporta el `logger` para que el resto del codigo `core/` lo importe
desde un solo lugar, como pide el estandar lambda-controller.

NOTA: este modulo NO usa `from __future__ import annotations`.
`BaseSettings` inspecciona `__annotations__` en runtime y compara
`field_type is str`; con anotaciones lazy (PEP 563) los tipos quedan
como strings (`'str'`) y la carga de env vars no detectaria los
campos. Las anotaciones deben ser los tipos reales.
"""

from enum import Enum

from shared.lambda_kit import BaseSettings
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

    # External API errors (5000-5999)
    EXTERNAL_API_ERROR = 5000
    DB_QUERY_FAILED = 5100

    # System / unexpected errors (6000+)
    UNEXPECTED_ERROR = 6000


class LogMetricType(Enum):
    """Tipos de metrica para logging estructurado del worker.

    Cada log estructurado lleva un `metric_type` en su `extra`, lo que
    permite construir metricas y filtros en CloudWatch.
    """

    # Lambda lifecycle
    LAMBDA_START = 'LAMBDA_START'
    LAMBDA_SUCCESS = 'LAMBDA_SUCCESS'
    LAMBDA_UNEXPECTED_ERROR = 'LAMBDA_UNEXPECTED_ERROR'

    # Worker batch lifecycle
    BATCH_RECEIVED = 'BATCH_RECEIVED'
    BATCH_PROCESSED = 'BATCH_PROCESSED'
    MESSAGE_MALFORMED = 'MESSAGE_MALFORMED'
    MESSAGE_PROCESSED = 'MESSAGE_PROCESSED'
    MESSAGE_FAILED = 'MESSAGE_FAILED'


class AppConfig(BaseSettings):
    """Configuracion del Lambda `tracking_worker`, desde env vars.

    Cada campo anotado se carga de la env var homonima en MAYUSCULAS.
    Los campos reales (connection string Neon, tabla cache) los
    resuelven `shared.db.url` y `shared.cache` directo desde su env
    var dedicada — aqui solo viven los toggles del Lambda.
    """

    environment: str = 'dev'

    # Testing
    testing: str = '0'

    def is_testing(self) -> bool:
        """Devuelve True si el servicio corre en modo testing."""
        return self.testing == '1'


# Singleton de configuracion: se evalua una vez en el cold start.
app_config = AppConfig()
