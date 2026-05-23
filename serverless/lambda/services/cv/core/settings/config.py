"""Configuracion del Lambda `cv`.

Define `AppConfig` (env vars), enums de codigos de error y de metricas,
y reexporta el `logger` de la libreria comun.
"""

from enum import Enum

from shared.lambda_kit import BaseSettings
from shared.observability.logger import logger

__all__ = ['AppConfig', 'ErrorCode', 'LogMetricType', 'app_config', 'logger']


class ErrorCode(Enum):
    """Codigos de error internos."""

    SUCCESS = 0
    VALIDATION_ERROR = 1000
    VALIDATION_FIELD_INVALID = 1002
    CONFIGURATION_ERROR = 2000
    EXTERNAL_API_ERROR = 5000
    UNEXPECTED_ERROR = 6000


class LogMetricType(Enum):
    """Tipos de metrica para logging estructurado."""

    LAMBDA_START = 'LAMBDA_START'
    LAMBDA_SUCCESS = 'LAMBDA_SUCCESS'
    LAMBDA_UNEXPECTED_ERROR = 'LAMBDA_UNEXPECTED_ERROR'
    PHASE_START = 'PHASE_START'
    PHASE_COMPLETE = 'PHASE_COMPLETE'
    CV_QUERY_OK = 'CV_QUERY_OK'
    CV_QUERY_ERROR = 'CV_QUERY_ERROR'


class AppConfig(BaseSettings):
    """Config del Lambda `cv`. La inyecta devtools desde el manifiesto."""

    environment: str = 'dev'

    # Whitelist CORS (CSV). La inyecta StageConfig del manifiesto.
    cors_allowed_origins: str = ''

    # Tabla DynamoDB de cache (la inyecta el manifest via SSM path).
    cache_table_name: str = ''

    # Path SSM de la connection string de Neon.
    ssm_neon_url_path: str = '/portfolio/neon-url'

    # Testing
    testing: str = '0'

    def is_testing(self) -> bool:
        """Devuelve True si el servicio corre en modo testing."""
        return self.testing == '1'


# Singleton de configuracion.
app_config = AppConfig()
