"""
Subpaquete `aws`: clientes boto3 de los servicios AWS del backend.

Agrupa los singletons de DynamoDB (Resource lazy), SES v2 (client module
scope) y SSM Parameter Store (con cache Powertools). Centralizar la
creacion de los clients evita reinstanciar boto3 en cada modulo y permite
resetear el cache en tests.

Convencion: importar SIEMPRE desde `shared.aws.<modulo>`.
"""

from shared.aws.dynamodb import get_resource, get_table, reset_resource_cache
from shared.aws.ses import ses
from shared.aws.ssm import clear_cache, get_parameter, get_secret

__all__ = [
    'clear_cache',
    'get_parameter',
    'get_resource',
    'get_secret',
    'get_table',
    'reset_resource_cache',
    'ses',
]
