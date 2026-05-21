"""Configuracion del Lambda `db`.

Define `AppConfig` (variables de entorno), los enums de codigos de error
y de metricas de logging, y reexporta el `logger` de la libreria comun.

El Lambda `db` usa el logger / tracer / metrics de Powertools v3 que vive
en `shared/` (vendorizado en `core/shared/` por devtools). `config.py`
reexporta el `logger` para que el resto del codigo `core/` lo importe
desde un solo lugar, como pide el estandar lambda-controller.
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
    DOWNGRADE_NOT_CONFIRMED = 4001

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

    # Schema operations (dominio del Lambda db)
    SCHEMA_MIGRATE_START = 'SCHEMA_MIGRATE_START'
    SCHEMA_MIGRATE_SUCCESS = 'SCHEMA_MIGRATE_SUCCESS'
    SCHEMA_OPERATION_ERROR = 'SCHEMA_OPERATION_ERROR'


class AppConfig(BaseSettings):
    """Configuracion del Lambda `db`, cargada de variables de entorno.

    Cada campo anotado se carga de la env var homonima en MAYUSCULAS.
    """

    environment: str = 'dev'

    # Path SSM de la connection string de Neon. La Lambda la resuelve en
    # runtime (shared.db.url). NUNCA se hardcodea la URL.
    ssm_neon_url_path: str = ''

    # Testing
    testing: str = '0'

    def is_testing(self) -> bool:
        """Devuelve True si el servicio corre en modo testing."""
        return self.testing == '1'


# Singleton de configuracion: se evalua una vez en el cold start.
app_config = AppConfig()
