"""Configuracion del Lambda `cv`.

Define `AppConfig` (variables de entorno + secretos lazy desde SSM), los
enums de codigos de error y de metricas de logging, y reexporta el
`logger` de la libreria comun.

El Lambda sirve la operation publica `cv` (lectura) Y las operations
admin `content`/`publish` (absorbidas del ex Lambda cv_admin en el plan
d-cv-consolidation): por eso la config combina los campos de lectura
(cache, neon) con los del dominio admin (JWT, blacklist, rate-limit,
github-deploy-token). Los secretos se exponen como `@cached_property`:
el primer acceso resuelve via `shared.aws.get_secret_by_name` (en cloud
lee SSM, en local lee env var directa).
"""

from __future__ import annotations

import os
from enum import Enum
from functools import cached_property

from shared.aws.ssm import get_parameter, get_secret_by_name
from shared.lambda_kit.base_settings import BaseSettings
from shared.observability.logger import logger

__all__ = ['AppConfig', 'ErrorCode', 'LogMetricType', 'app_config', 'logger']


class ErrorCode(Enum):
    """Codigos de error internos, agrupados por rango.

    0 exito; 1xxx validacion; 2xxx configuracion; 4xxx negocio; 5xxx
    API/externo; 6xxx sistema. El handler colapsa el `code` del controller
    a un HTTP status estable.
    """

    SUCCESS = 0

    # Validation errors (1000-1999)
    VALIDATION_ERROR = 1000
    VALIDATION_FIELD_INVALID = 1002
    UNKNOWN_NICHE = 1100
    REORDER_SLUGS_MISMATCH = 1101

    # Configuration errors (2000-2999)
    CONFIGURATION_ERROR = 2000
    CONFIGURATION_MISSING = 2001

    # Business logic errors (4000-4999)
    BUSINESS_LOGIC_ERROR = 4000
    SLUG_NOT_FOUND = 4404
    RATE_LIMIT_EXCEEDED = 4090

    # External API errors (5000-5999)
    EXTERNAL_API_ERROR = 5000
    GITHUB_API_ERROR = 5200

    # System / unexpected errors (6000+)
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

    # Dominio admin (operations content/publish, ex cv_admin)
    CV_ADMIN_CONTENT_WRITTEN = 'CV_ADMIN_CONTENT_WRITTEN'
    CV_ADMIN_CONTENT_DELETED = 'CV_ADMIN_CONTENT_DELETED'
    CV_ADMIN_PUBLISH_DISPATCHED = 'CV_ADMIN_PUBLISH_DISPATCHED'
    CV_ADMIN_ADMIN_DENIED = 'CV_ADMIN_ADMIN_DENIED'
    CV_ADMIN_OPERATION_ERROR = 'CV_ADMIN_OPERATION_ERROR'


def _resolve_from_ssm(env_var_name: str) -> str:
    """Resuelve un valor desde SSM leyendo el path de una env var.

    `env_var_name` (ej. `SSM_JWT_BLACKLIST_TABLE_PATH`) contiene el path
    SSM. En local permitimos override directo via la misma env var con un
    valor plano (mismo patron que auth/users).
    """
    raw = os.environ.get(env_var_name, '')
    if not raw:
        return ''
    if raw.startswith('/'):
        return get_parameter(raw)
    return raw


class AppConfig(BaseSettings):
    """Config del Lambda `cv`, cargada de env vars + SSM lazy."""

    environment: str = 'dev'

    # Whitelist CORS (CSV). La inyecta StageConfig del manifiesto.
    cors_allowed_origins: str = ''

    # Tabla DynamoDB de cache (la inyecta el manifest via SSM path).
    cache_table_name: str = ''

    # Path SSM de la connection string de Neon.
    ssm_neon_url_path: str = '/portfolio/neon-url'

    # JWT (operations admin)
    jwt_issuer: str = 'portfolio-auth'
    jwt_audience: str = 'portfolio'

    # Testing
    testing: str = '0'

    def is_testing(self) -> bool:
        """Devuelve True si el servicio corre en modo testing."""
        return self.testing == '1'

    # ----- Secretos lazy desde SSM (cold start) -----

    @cached_property
    def jwt_secret(self) -> str:
        """JWT HS256 secret (SecureString + KMS en SSM)."""
        return get_secret_by_name('jwt-secret', local_env='JWT_SECRET')

    @cached_property
    def neon_url(self) -> str:
        """Connection string PostgreSQL (Neon, schema cv_* + auth_*)."""
        return get_secret_by_name('neon-url', local_env='DB_URL')

    # ----- Nombres de recursos resueltos en cold start desde SSM -----

    @cached_property
    def jwt_blacklist_table_name(self) -> str:
        """Tabla DynamoDB de jti blacklisted (solo lookup)."""
        return _resolve_from_ssm('SSM_JWT_BLACKLIST_TABLE_PATH')

    @cached_property
    def rate_limit_rules_table_name(self) -> str:
        """Tabla DynamoDB con las rate-limit rules."""
        return _resolve_from_ssm('SSM_RATE_LIMIT_RULES_TABLE_PATH')

    @cached_property
    def rate_limit_buckets_table_name(self) -> str:
        """Tabla DynamoDB con los sliding-window buckets."""
        return _resolve_from_ssm('SSM_RATE_LIMIT_BUCKETS_TABLE_PATH')


# Singleton de configuracion: se evalua una vez en el cold start (los
# secretos siguen siendo lazy via @cached_property).
app_config = AppConfig()
