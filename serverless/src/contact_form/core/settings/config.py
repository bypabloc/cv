"""Configuracion del Lambda `contact_form`.

Define `AppConfig` (variables de entorno), los enums de codigos de error
y de metricas de logging, y reexporta el `logger` de la libreria comun.

El Lambda `contact_form` usa el logger / tracer / metrics de Powertools
v3 que vive en `shared/` (vendorizado en `core/shared/` por devtools).
`config.py` reexporta el `logger` para que el resto del codigo `core/`
lo importe desde un solo lugar, como pide el estandar lambda-controller.
"""

from enum import Enum

from shared.logger import logger
from utils.base_settings import BaseSettings

__all__ = ['AppConfig', 'ErrorCode', 'LogMetricType', 'app_config', 'logger']


class ErrorCode(Enum):
    """Codigos de error internos, agrupados por rango.

    0 exito; 1xxx validacion; 2xxx configuracion; 4xxx negocio; 5xxx
    API/externo; 6xxx sistema. El handler colapsa el `code` del
    controller a un HTTP status estable.
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
    RATE_LIMIT_EXCEEDED = 4001
    CAPTCHA_INVALID = 4002

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

    # Contact operations (dominio del Lambda contact_form)
    CONTACT_RATE_LIMITED = 'CONTACT_RATE_LIMITED'
    CONTACT_CAPTCHA_FAILED = 'CONTACT_CAPTCHA_FAILED'
    CONTACT_PERSISTED = 'CONTACT_PERSISTED'
    CONTACT_EMAIL_SENT = 'CONTACT_EMAIL_SENT'
    CONTACT_OPERATION_ERROR = 'CONTACT_OPERATION_ERROR'


class AppConfig(BaseSettings):
    """Configuracion del Lambda `contact_form`, cargada de env vars.

    Cada campo anotado se carga de la env var homonima en MAYUSCULAS.
    Las tablas DynamoDB y los paths SSM los inyecta el template SAM; los
    secretos NUNCA se hardcodean — solo se guarda su path SSM.
    """

    environment: str = 'dev'

    # Region donde vive la identidad SES verificada.
    aws_ses_region: str = 'us-east-1'

    # Whitelist CORS (CSV). La inyecta StageConfig del template SAM.
    cors_allowed_origins: str = ''

    # Tablas DynamoDB (las inyecta el template SAM desde el stack de infra).
    contacts_table_name: str = ''
    cache_table_name: str = ''
    rate_limit_rules_table_name: str = ''
    rate_limit_buckets_table_name: str = ''

    # Paths SSM de los secretos / parametros (la Lambda los resuelve en
    # runtime via boto3; NUNCA se guarda el valor del secreto aqui).
    ssm_turnstile_secret_path: str = '/portfolio/turnstile-secret'
    ssm_turnstile_bypass_path: str = ''
    ssm_owner_email_path: str = '/portfolio/owner-email'
    ssm_ses_from_path: str = '/portfolio/ses-from-address'

    # Testing
    testing: str = '0'

    def is_testing(self) -> bool:
        """Devuelve True si el servicio corre en modo testing."""
        return self.testing == '1'


# Singleton de configuracion: se evalua una vez en el cold start.
app_config = AppConfig()
