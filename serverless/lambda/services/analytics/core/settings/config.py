"""Configuracion del Lambda `analytics`.

`AppConfig` (env vars + secretos lazy desde SSM), enums de codigos de error
y de metricas, y reexporta el `logger` de la libreria comun.

Los secretos (`jwt_secret`, `neon_url`) se exponen como `@cached_property`:
el primer acceso resuelve el valor via `shared.aws.get_secret_by_name` (en
cloud lee SSM, en local lee la env var fallback). Los nombres de tabla
DynamoDB se resuelven en el cold start desde el path SSM que devtools inyecta
como env var (`SSM_<TABLA>_TABLE_PATH`).
"""

from __future__ import annotations

from enum import Enum, IntEnum
from functools import cached_property
from os import environ

from shared.aws.ssm import get_parameter, get_secret_by_name
from shared.observability.logger import logger

__all__ = ['AppConfig', 'ErrorCode', 'LogMetricType', 'app_config', 'logger']


class ErrorCode(IntEnum):
    """Codigos de error internos -> HTTP status (lo mapea http_handler)."""

    OK = 0
    VALIDATION = 1000
    DATE_RANGE = 1001
    PAGE_SIZE = 1002
    INVALID_PARAM = 1003
    UNAUTHORIZED = 4010
    BLACKLISTED = 4030
    COUNTRY_BLOCKED = 4031
    NOT_FOUND = 4040
    RATE_LIMITED = 4290
    EXTERNAL = 5100
    INTERNAL = 6000


class LogMetricType(Enum):
    """Tipos de metrica para logging estructurado."""

    QUERY_OK = 'AnalyticsQueryOk'
    QUERY_REJECTED = 'AnalyticsQueryRejected'
    QUERY_ERROR = 'AnalyticsQueryError'
    CACHE_HIT = 'AnalyticsCacheHit'
    CACHE_MISS = 'AnalyticsCacheMiss'


def _resolve_from_ssm(env_var: str) -> str:
    """Resuelve un nombre de recurso desde el path SSM inyectado por devtools.

    devtools inyecta `SSM_<TABLA>_TABLE_PATH=/portfolio/<stage>/dynamodb/...`.
    Si el valor empieza con `/` se resuelve via SSM; sino se usa tal cual
    (util en tests con un nombre literal).
    """
    raw = environ.get(env_var, '')
    if not raw:
        return ''
    if raw.startswith('/'):
        return get_parameter(raw)
    return raw


class AppConfig:
    """Config del Lambda `analytics`. La inyecta devtools desde el manifiesto.

    No hereda de BaseSettings: lee las env vars directamente para poder usar
    `@cached_property` (secretos + tablas lazy) sin chocar con la carga
    automatica de campos anotados.
    """

    def __init__(self) -> None:
        self.environment = environ.get('ENVIRONMENT', 'dev')
        self.jwt_issuer = environ.get('JWT_ISSUER', 'portfolio-auth')
        self.jwt_audience = environ.get('JWT_AUDIENCE', 'portfolio')
        self.cors_allowed_origins = environ.get('CORS_ALLOWED_ORIGINS', '')
        self.rate_limit_endpoint = environ.get(
            'RATE_LIMIT_ENDPOINT', '/analytics'
        )
        self.date_default_days = int(
            environ.get('ANALYTICS_DATE_DEFAULT_DAYS', '30')
        )
        self.date_max_days = int(environ.get('ANALYTICS_DATE_MAX_DAYS', '90'))
        self.page_size_default = int(
            environ.get('ANALYTICS_PAGE_SIZE_DEFAULT', '50')
        )
        self.page_size_max = int(environ.get('ANALYTICS_PAGE_SIZE_MAX', '200'))
        self.cache_ttl_aggregate = int(
            environ.get('ANALYTICS_CACHE_TTL_AGGREGATE', '60')
        )
        self.cache_ttl_live = int(environ.get('ANALYTICS_CACHE_TTL_LIVE', '10'))
        self.testing = environ.get('TESTING', '0')

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
        """Connection string PostgreSQL (Neon, schema vis_* + tax_*)."""
        return get_secret_by_name('neon-url', local_env='DB_URL')

    # ----- Nombres de recursos resueltos en cold start desde SSM -----

    @cached_property
    def cache_table_name(self) -> str:
        """Tabla DynamoDB de cache (@cached)."""
        return _resolve_from_ssm('SSM_CACHE_TABLE_PATH')

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
