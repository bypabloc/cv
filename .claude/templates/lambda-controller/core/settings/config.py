"""
Configuracion del servicio Lambda.

Define AppConfig (variables de entorno), los enums de codigos de error
y de metricas de logging, y el logger singleton.

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

from enum import Enum

from utils.base_settings import BaseSettings
from utils.logger import Logger

# Logger del servicio. Los argumentos posicionales son las keys de
# contexto que se adjuntan a cada log (ver Logger.basic_loader).
logger = Logger()


class ErrorCode(Enum):
    """
    Codigos de error internos, agrupados por rango.

    Rango        Significado
    -----        -----------
    0            Exito
    1000-1999    Errores de validacion
    2000-2999    Errores de configuracion
    4000-4999    Errores de logica de negocio
    5000-5999    Errores de API / servicios externos
    6000+        Errores de sistema / inesperados

    :Authors:
        - <Autor>

    :Created:
        - YYYY-MM-DD
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
    EXTERNAL_API_TIMEOUT = 5001
    EXTERNAL_API_CONNECTION = 5002
    LAMBDA_INVOKE_ERROR = 5003

    # System / unexpected errors (6000+)
    UNEXPECTED_ERROR = 6000


class LogMetricType(Enum):
    """
    Tipos de metrica para logging estructurado.

    Cada log estructurado lleva un metric_type en su extra, lo que
    permite construir metricas y filtros en CloudWatch.

    :Authors:
        - <Autor>

    :Created:
        - YYYY-MM-DD
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

    # Downstream lambda invocation
    LAMBDA_INVOKE_START = 'LAMBDA_INVOKE_START'
    LAMBDA_INVOKE_SUCCESS = 'LAMBDA_INVOKE_SUCCESS'
    LAMBDA_INVOKE_FAILED = 'LAMBDA_INVOKE_FAILED'

    # Business operation (renombrar al dominio del servicio)
    OPERATION_START = 'OPERATION_START'
    OPERATION_SUCCESS = 'OPERATION_SUCCESS'
    OPERATION_ERROR = 'OPERATION_ERROR'


class AppConfig(BaseSettings):
    """
    Configuracion del servicio, cargada desde variables de entorno.

    Cada campo anotado se carga de la env var homonima en MAYUSCULAS.
    Agregar aqui los ARNs de Lambdas downstream y demas parametros.

    :Authors:
        - <Autor>

    :Created:
        - YYYY-MM-DD
    """

    environment: str = 'dev'

    # ARNs de lambdas downstream (uno por cada arn_config_key usado en
    # los controllers). Eliminar si el servicio no invoca otros Lambdas.
    arn_example: str = ''

    # Testing
    testing: str = '0'

    def is_testing(self) -> bool:
        """Devuelve True si el servicio corre en modo testing."""
        return self.testing == '1'

    class Config:
        """Config de carga de entorno."""

        env_file_encoding = 'utf-8'


# Singleton de configuracion: se evalua una vez en el cold start.
app_config = AppConfig()
