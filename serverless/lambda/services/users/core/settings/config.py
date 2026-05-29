"""Configuracion del Lambda `users`.

Define `AppConfig` (variables de entorno + secretos lazy desde SSM), los
enums de codigos de error y de metricas de logging, y reexporta el
`logger` de la libreria comun.

Los secretos se exponen como `@cached_property`: el primer acceso resuelve
el valor via `shared.aws.get_secret_by_name` (en cloud lee SSM, en local
lee env var directa) y se cachea para el resto del lifecycle del
contenedor. Los nombres de tabla DynamoDB se resuelven leyendo los paths
SSM publicados por el provisioner. Clona el patron de `auth`.
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
    VALIDATION_FIELD_REQUIRED = 1001
    VALIDATION_FIELD_INVALID = 1002

    # Configuration errors (2000-2999)
    CONFIGURATION_ERROR = 2000
    CONFIGURATION_MISSING = 2001

    # Business logic errors (4000-4999)
    BUSINESS_LOGIC_ERROR = 4000
    NOT_FOUND = 4001
    CANNOT_DISABLE_SELF = 4002
    CANNOT_DELETE_SELF = 4003
    EMAIL_ALREADY_IN_USE = 4004
    INVALID_PASSWORD = 4005
    CANNOT_REVOKE_CURRENT_SESSION = 4006
    USER_NOT_DISABLED = 4007
    INVALID_CONFIRM_SENTINEL = 4008
    CANNOT_DELETE_ADMIN_ACCOUNT = 4009
    ACCOUNT_DISABLED = 4030
    ACCOUNT_LOCKED = 4031

    # Cross-cutting business
    RATE_LIMIT_EXCEEDED = 4090

    # External API errors (5000-5999)
    EXTERNAL_API_ERROR = 5000
    QUEUE_PUBLISH_FAILED = 5001
    NEON_WRITE_FAILED = 5002

    # System / unexpected errors (6000+)
    UNEXPECTED_ERROR = 6000


class LogMetricType(Enum):
    """Tipos de metrica para logging estructurado."""

    LAMBDA_START = 'LAMBDA_START'
    LAMBDA_SUCCESS = 'LAMBDA_SUCCESS'
    LAMBDA_UNEXPECTED_ERROR = 'LAMBDA_UNEXPECTED_ERROR'
    PHASE_START = 'PHASE_START'
    PHASE_COMPLETE = 'PHASE_COMPLETE'

    # Users domain
    USERS_PROFILE_UPDATED = 'USERS_PROFILE_UPDATED'
    USERS_PROFILE_DELETED = 'USERS_PROFILE_DELETED'
    USERS_EMAIL_CHANGE_REQUESTED = 'USERS_EMAIL_CHANGE_REQUESTED'
    USERS_SESSION_REVOKED = 'USERS_SESSION_REVOKED'
    USERS_ADMIN_ACTION = 'USERS_ADMIN_ACTION'
    USERS_ADMIN_DENIED = 'USERS_ADMIN_DENIED'
    USERS_OPERATION_ERROR = 'USERS_OPERATION_ERROR'


def _resolve_from_ssm(env_var_name: str) -> str:
    """Resuelve un valor desde SSM leyendo el path de una env var.

    `env_var_name` (ej. `SSM_JWT_BLACKLIST_TABLE_PATH`) contiene el path
    SSM. En local permitimos override directo via la misma env var con un
    valor plano (mismo patron que auth/contact_form).
    """
    raw = os.environ.get(env_var_name, '')
    if not raw:
        return ''
    if raw.startswith('/'):
        return get_parameter(raw)
    return raw


class AppConfig(BaseSettings):
    """Configuracion del Lambda `users`, cargada de env vars + SSM lazy."""

    environment: str = 'dev'

    # JWT
    jwt_issuer: str = 'portfolio-auth'
    jwt_audience: str = 'portfolio'

    # CORS (whitelist CSV)
    cors_allowed_origins: str = ''

    # Base URL del propio Lambda (para el verify_url del change-email).
    users_base_url: str = ''

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
        """Connection string PostgreSQL (Neon, schema auth_*)."""
        return get_secret_by_name('neon-url', local_env='DB_URL')

    @cached_property
    def ses_from_address(self) -> str:
        """From verificado en SES (lo usa el worker via SQS payload)."""
        return get_secret_by_name(
            'ses-from-address',
            local_env='SES_FROM_ADDRESS',
        )

    # ----- Nombres de recursos resueltos en cold start desde SSM -----

    @cached_property
    def jwt_blacklist_table_name(self) -> str:
        """Tabla DynamoDB de jti blacklisted (GSI by_family_id)."""
        return _resolve_from_ssm('SSM_JWT_BLACKLIST_TABLE_PATH')

    @cached_property
    def rate_limit_rules_table_name(self) -> str:
        """Tabla DynamoDB con las rate-limit rules."""
        return _resolve_from_ssm('SSM_RATE_LIMIT_RULES_TABLE_PATH')

    @cached_property
    def rate_limit_buckets_table_name(self) -> str:
        """Tabla DynamoDB con los sliding-window buckets."""
        return _resolve_from_ssm('SSM_RATE_LIMIT_BUCKETS_TABLE_PATH')

    @cached_property
    def auth_email_queue_url(self) -> str:
        """URL SQS de la cola hacia el `auth_email_worker`."""
        return _resolve_from_ssm('SSM_AUTH_EMAIL_QUEUE_URL_PATH')


# Singleton de configuracion: se evalua una vez en el cold start (los
# secretos siguen siendo lazy via @cached_property).
app_config = AppConfig()
