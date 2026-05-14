"""
DynamoDB Resource API client.

Decision (.claude/docs/aws-lambda/04-cold-start-optimization.md):
boto3 Resource/Client en MODULE SCOPE (no en handler) reduce cold start
~150ms en invocaciones warm. La conexion HTTPS + STS roles se reusan.

Usar SIEMPRE `Resource` (mas alto nivel) para CRUD; Client crudo solo si
no hay Resource equivalente.

Uso:
    from common.dynamodb_client import dynamodb, get_table

    table = get_table('portfolio-contacts-dev')
    table.put_item(Item={...})
"""

from __future__ import annotations

import os
from typing import Any

import boto3

# Region desde env var AWS_REGION (default us-east-1 desde Settings).
# NO usar boto3.Session() porque crea connection pool nuevo cada vez.
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))


def get_table(table_name: str) -> Any:
    """
    Helper para obtener una Table reference. Es equivalente a
    `dynamodb.Table(name)` pero centraliza la importacion.

    Args:
        table_name: nombre fisico de la tabla DynamoDB.

    Returns:
        boto3 DynamoDB Table reference.
    """
    return dynamodb.Table(table_name)
