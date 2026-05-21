"""
Common module: helpers compartidos entre todas las Lambdas del backend.

Re-exports:
- logger, tracer, metrics: instancias Powertools v3 configuradas
- dynamodb_resource, ssm_client, ses_client: boto3 clients en module scope
- BaseModel: clase base del ORM DynamoDB (ver shared/dynamodb/)
- extract_ip, new_uuidv7, is_valid_email: utilities sin estado
- json_response, error_response, cors_headers: HTTP helpers
- ApplicationError + subclases: jerarquia de excepciones
- Settings: configuracion desde env vars (Pydantic)

Convencion: importar SIEMPRE desde `shared.<submodulo>` (no este __init__)
para evitar imports circulares en tests. Este modulo solo expone la API
publica para uso ergonomico.
"""

from shared.dynamodb import BaseModel
from shared.exceptions import (
    ApplicationError,
    IPBlacklistedError,
    RateLimitExceededError,
    TurnstileError,
    ValidationError,
)
from shared.ip_extractor import extract_ip
from shared.responses import error_response, json_response
from shared.ulid import new_uuidv7
from shared.validators import is_valid_email, sanitize_text

__all__ = [
    'ApplicationError',
    'BaseModel',
    'IPBlacklistedError',
    'RateLimitExceededError',
    'TurnstileError',
    'ValidationError',
    'error_response',
    'extract_ip',
    'is_valid_email',
    'json_response',
    'new_uuidv7',
    'sanitize_text',
]
