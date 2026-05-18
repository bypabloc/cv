"""
DynamoDB Resource API client.

Decision (.claude/docs/aws-lambda/04-cold-start-optimization.md):
boto3 Resource/Client SINGLETON reusado entre invocaciones reduce cold
start ~150ms en invocaciones warm. La conexion HTTPS + STS roles se
reusan.

El resource se crea de forma LAZY (en el primer `get_table`/`get_resource`,
no al importar el modulo). Motivo: crearlo en module scope lo ataria a las
credenciales presentes en el import, lo que rompe `moto` en tests (el mock
se activa DESPUES del import). Lazy + cache da el mismo beneficio en Lambda
-el primer uso ocurre en el cold start, igual que un import- y deja que
`moto` intercepte la creacion cuando el mock ya esta activo.

Usar SIEMPRE `Resource` (mas alto nivel) para CRUD; Client crudo solo si
no hay Resource equivalente.

Uso:
    from common.dynamodb_client import get_table

    table = get_table('portfolio-contacts-dev')
    table.put_item(Item={...})
"""

from __future__ import annotations

import os
from typing import Any

import boto3

# Singleton cacheado. None hasta el primer get_resource().
_dynamodb_resource: Any = None


def get_resource() -> Any:
    """
    Resource DynamoDB singleton (creado lazy en el primer uso).

    Se cachea a nivel de modulo: la primera llamada lo crea, las siguientes
    reusan la misma instancia (conexion HTTPS + credenciales compartidas
    entre invocaciones warm del mismo contenedor Lambda).

    Returns:
        boto3 DynamoDB ServiceResource.
    """
    global _dynamodb_resource
    if _dynamodb_resource is None:
        region = os.environ.get('AWS_REGION', 'us-east-1')
        # NO usar boto3.Session(): crearia un connection pool nuevo.
        _dynamodb_resource = boto3.resource('dynamodb', region_name=region)
    return _dynamodb_resource


def get_table(table_name: str) -> Any:
    """
    Table reference sobre el resource singleton.

    Args:
        table_name: nombre fisico de la tabla DynamoDB.

    Returns:
        boto3 DynamoDB Table reference.
    """
    return get_resource().Table(table_name)


def reset_resource_cache() -> None:
    """
    Limpia el resource cacheado. Solo para aislamiento entre tests:
    fuerza que el proximo `get_resource()` cree uno nuevo bajo el
    `mock_aws()` activo del test.
    """
    global _dynamodb_resource
    _dynamodb_resource = None
