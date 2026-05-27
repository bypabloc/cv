"""
Subpaquete `aws`: clientes boto3 de los servicios AWS del backend.

Agrupa los singletons de DynamoDB (Resource lazy), SES v2 (client module
scope), SSM Parameter Store (con cache Powertools) y los helpers de tipos
de DynamoDB. Centralizar la creacion de los clients evita reinstanciar
boto3 en cada modulo y permite resetear el cache en tests.

Actua como portador unico de boto3 para el backend: los `core/` de los
services NO importan `boto3` directo — usan los wrappers de aqui
(ver `.claude/rules/lambda-shared-imports.md`).

Convencion: importar SIEMPRE desde `shared.aws` (o `shared.aws.<modulo>`
si se necesita un simbolo no re-exportado).
"""

from shared.aws.dynamodb import get_resource, get_table, reset_resource_cache
from shared.aws.dynamodb_types import TypeDeserializer, TypeSerializer
from shared.aws.ses import send_email, ses
from shared.aws.ssm import (
    clear_cache,
    get_parameter,
    get_secret,
    get_secret_by_name,
)

__all__ = [
    'TypeDeserializer',
    'TypeSerializer',
    'clear_cache',
    'get_parameter',
    'get_resource',
    'get_secret',
    'get_secret_by_name',
    'get_table',
    'reset_resource_cache',
    'send_email',
    'ses',
]
