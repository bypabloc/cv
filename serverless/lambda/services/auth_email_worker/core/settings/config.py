"""Configuracion del Lambda `auth_email_worker`.

Define `AppConfig` (variables de entorno), los enums de codigos de error
y de metricas de logging, y reexporta el `logger` de la libreria comun.

El Lambda usa el logger / metrics de Powertools v3 que vive en
`shared/` (vendorizado en `core/shared/` por devtools). `config.py`
reexporta el `logger` para que el resto del codigo `core/` lo importe
desde un solo lugar, como pide el estandar lambda-controller.
"""

from enum import Enum

from shared.lambda_kit import BaseSettings
from shared.observability.logger import logger

__all__ = ['AppConfig', 'ErrorCode', 'LogMetricType', 'app_config', 'logger']


class ErrorCode(Enum):
    """Codigos de error internos, agrupados por rango.

    0 exito; 1xxx validacion; 2xxx configuracion; 4xxx negocio; 5xxx
    API/externo; 6xxx sistema. El handler colapsa el `code` del controller
    a un comportamiento de SQS estable (mensaje OK = ack, mensaje fallido
    = batchItemFailure para reintento).
    """

    SUCCESS = 0

    # Validation errors (1000-1999)
    VALIDATION_ERROR = 1000
    VALIDATION_FIELD_REQUIRED = 1001
    VALIDATION_FIELD_INVALID = 1002
    VALIDATION_UNKNOWN_KIND = 1003

    # Configuration errors (2000-2999)
    CONFIGURATION_ERROR = 2000
    CONFIGURATION_MISSING = 2001
    TEMPLATE_NOT_FOUND = 2002

    # Business logic errors (4000-4999)
    BUSINESS_LOGIC_ERROR = 4000

    # External API errors (5000-5999)
    EXTERNAL_API_ERROR = 5000
    SES_SEND_FAILED = 5001
    SES_THROTTLED = 5002
    NEON_WRITE_FAILED = 5003

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

    # Email worker operations (dominio del Lambda auth_email_worker)
    EMAIL_MESSAGE_RECEIVED = 'EMAIL_MESSAGE_RECEIVED'
    EMAIL_TEMPLATE_RENDERED = 'EMAIL_TEMPLATE_RENDERED'
    EMAIL_SENT = 'EMAIL_SENT'
    EMAIL_SEND_FAILED = 'EMAIL_SEND_FAILED'
    EMAIL_AUDIT_FAILED = 'EMAIL_AUDIT_FAILED'


class AppConfig(BaseSettings):
    """Configuracion del Lambda `auth_email_worker`, cargada de env vars.

    Cada campo anotado se carga de la env var homonima en MAYUSCULAS.
    Los secretos NUNCA se hardcodean — solo se guarda su path SSM (el
    codigo lee el valor en runtime).
    """

    environment: str = 'dev'

    # Region donde vive la identidad SES verificada.
    aws_ses_region: str = 'us-east-1'

    # Paths SSM de los secretos / parametros (la Lambda los resuelve en
    # runtime via boto3; NUNCA se guarda el valor del secreto aqui).
    ssm_neon_url_path: str = '/portfolio/neon-url'
    ssm_ses_from_address_path: str = '/portfolio/ses-from-address'

    # Locale default (MVP plan 01-auth-infra-basics: solo es). Si en
    # futuros planes se agrega multi-locale, este campo se sobreescribe
    # via env var o el mensaje SQS aporta el locale.
    default_locale: str = 'es'

    # Testing
    testing: str = '0'

    def is_testing(self) -> bool:
        """Devuelve True si el servicio corre en modo testing."""
        return self.testing == '1'


# Singleton de configuracion: se evalua una vez en el cold start.
app_config = AppConfig()
