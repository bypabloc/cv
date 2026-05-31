"""Configuracion del Lambda `auth`.

Define `AppConfig` (variables de entorno + secretos lazy desde SSM), los
enums de codigos de error y de metricas de logging, y reexporta el
`logger` de la libreria comun.

Los secretos se exponen como `@cached_property` para evitar IO en cold
start si una request determinada no los necesita (ej. el health check
nunca lee `jwt_secret`). El primer acceso resuelve el secret via
`shared.aws.get_secret_by_name` (en cloud lee SSM, en local lee env
var directa) y se cachea para el resto del lifecycle del contenedor.

Los nombres de tabla DynamoDB y URLs SQS se resuelven en cold start
leyendo los paths SSM publicados por el provisioner — el patron clona
el de `contact_form/core/settings/config.py`.
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

    # Domain-specific auth errors (4001-4099)
    EMAIL_NOT_FOUND = 4001
    EMAIL_ALREADY_REGISTERED = 4002
    TOKEN_BLACKLISTED = 4003
    TOKEN_REUSE_DETECTED = 4004
    ACCOUNT_LOCKED = 4005
    LINK_CONSUMED = 4006
    LINK_EXPIRED = 4007
    INVALID_CODE = 4008
    MAX_ATTEMPTS_EXCEEDED = 4009
    RESEND_THROTTLED = 4010
    PENDING_VERIFICATION = 4011

    # Cross-cutting business (compartido con otros Lambdas)
    RATE_LIMIT_EXCEEDED = 4090
    CAPTCHA_INVALID = 4091

    # External API errors (5000-5999)
    EXTERNAL_API_ERROR = 5000
    QUEUE_PUBLISH_FAILED = 5001
    NEON_WRITE_FAILED = 5002

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

    # Auth operations (dominio del Lambda auth)
    AUTH_RATE_LIMITED = 'AUTH_RATE_LIMITED'
    AUTH_CAPTCHA_FAILED = 'AUTH_CAPTCHA_FAILED'
    AUTH_USER_CREATED = 'AUTH_USER_CREATED'
    AUTH_LOGIN_OK = 'AUTH_LOGIN_OK'
    AUTH_LOGIN_FAILED = 'AUTH_LOGIN_FAILED'
    AUTH_LOGOUT = 'AUTH_LOGOUT'
    AUTH_TOKEN_ISSUED = 'AUTH_TOKEN_ISSUED'  # noqa: S105 (enum name, no secreto)
    AUTH_TOKEN_BLACKLISTED = 'AUTH_TOKEN_BLACKLISTED'  # noqa: S105
    AUTH_TOKEN_REUSE_DETECTED = 'AUTH_TOKEN_REUSE_DETECTED'  # noqa: S105
    AUTH_MAGIC_LINK_ISSUED = 'AUTH_MAGIC_LINK_ISSUED'
    AUTH_CODE_ISSUED = 'AUTH_CODE_ISSUED'
    AUTH_OPERATION_ERROR = 'AUTH_OPERATION_ERROR'


def _resolve_from_ssm(env_var_name: str) -> str:
    """Resuelve un valor desde SSM leyendo el path de una env var.

    `env_var_name`: nombre de la env var (ej.
    `SSM_JWT_BLACKLIST_TABLE_PATH`) que contiene el path SSM. En local
    permitimos override directo via la misma env var con un valor
    plano (mismo patron que contact_form).
    """
    raw = os.environ.get(env_var_name, '')
    if not raw:
        return ''
    if raw.startswith('/'):
        return get_parameter(raw)
    # Local mode: el valor ya es el nombre / URL directo.
    return raw


class AppConfig(BaseSettings):
    """Configuracion del Lambda `auth`, cargada de env vars + SSM lazy.

    Cada campo anotado se carga de la env var homonima en MAYUSCULAS.
    Los paths SSM los inyecta devtools desde el manifest; los secretos
    NUNCA se hardcodean — solo se guarda su path SSM (el codigo lee el
    valor en runtime via `get_secret_by_name`).
    """

    environment: str = 'dev'

    # JWT
    jwt_issuer: str = 'portfolio-auth'
    jwt_audience: str = 'portfolio'

    # CORS (whitelist CSV)
    cors_allowed_origins: str = ''

    # URLs del flujo de magic-link
    magic_link_base_url: str = ''
    dashboard_callback_url: str = ''

    # MFA / WebAuthn (plan 02)
    # KMS CMK directa para cifrar el TOTP secret (decision 1).
    kms_totp_key_id: str = 'alias/portfolio-lambdas'
    # WebAuthn: RP_ID = sufijo comun de los origins del env (decision 5).
    webauthn_rp_id: str = ''
    webauthn_rp_name: str = 'The Full Stack Portfolio'
    # CSV de origins permitidos en el ceremony WebAuthn (verify_origin).
    webauthn_allowed_origins: str = ''

    # Testing
    testing: str = '0'

    def is_testing(self) -> bool:
        """Devuelve True si el servicio corre en modo testing."""
        return self.testing == '1'

    @property
    def webauthn_origins(self) -> list[str]:
        """Lista de origins permitidos (CSV de WEBAUTHN_ALLOWED_ORIGINS)."""
        return [
            origin.strip()
            for origin in self.webauthn_allowed_origins.split(',')
            if origin.strip()
        ]

    # ----- Secretos lazy desde SSM (cold start) -----

    @cached_property
    def jwt_secret(self) -> str:
        """JWT HS256 secret (SecureString + KMS en SSM)."""
        return get_secret_by_name('jwt-secret', local_env='JWT_SECRET')

    @cached_property
    def turnstile_secret(self) -> str:
        """Cloudflare Turnstile secret key (SecureString + KMS)."""
        return get_secret_by_name(
            'turnstile-secret',
            local_env='TURNSTILE_SECRET_KEY',
        )

    @cached_property
    def neon_url(self) -> str:
        """Connection string PostgreSQL (Neon, schema auth_*)."""
        return get_secret_by_name('neon-url', local_env='DB_URL')

    # ----- Nombres de recursos resueltos en cold start desde SSM -----

    @cached_property
    def cache_table_name(self) -> str:
        """Tabla DynamoDB usada por Powertools cache."""
        return _resolve_from_ssm('SSM_CACHE_TABLE_PATH')

    @cached_property
    def jwt_blacklist_table_name(self) -> str:
        """Tabla DynamoDB de jti blacklisted (GSI by_family_id)."""
        return _resolve_from_ssm('SSM_JWT_BLACKLIST_TABLE_PATH')

    @cached_property
    def webauthn_challenges_table_name(self) -> str:
        """Tabla DynamoDB de challenges WebAuthn efimeros (TTL 5 min)."""
        return _resolve_from_ssm('SSM_WEBAUTHN_CHALLENGES_TABLE_PATH')

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
