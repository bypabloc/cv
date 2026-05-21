"""ORM minimalista para DynamoDB del backend serverless del portfolio.

Cada tabla del backend se modela como una subclase de `BaseModel`
(Pydantic) con un `Meta: TableMeta`. El `BaseModel` encapsula todo el
acceso boto3, reusa el resource singleton de `shared.dynamodb_client`,
convierte `Decimal` de forma transparente y expone DML (datos) + DDL
acotado (verificacion de esquema + create solo para tests/local).

Las tablas reales de dev/stage/prod las sigue creando CloudFormation
(`serverless/infra/infra.yaml`): es el unico que puede conectar el
DynamoDB Stream al `stream_processor` y exportar los `TableArn` para el
IAM least-privilege. Ver `README.md` de este paquete.

Uso ergonomico:

    from shared.dynamodb import ContactItem

    ContactItem(id='...', created_at='...', name='Pablo').save()
    item = ContactItem.get('the-id')
"""

from shared.dynamodb._schema import GSIMeta, SchemaDiff, TableMeta
from shared.dynamodb.base import BaseModel
from shared.dynamodb.models import (
    CacheItem,
    ContactItem,
    RateLimitBucketItem,
    RateLimitRuleItem,
    TrackingEventItem,
)

__all__ = [
    'BaseModel',
    'CacheItem',
    'ContactItem',
    'GSIMeta',
    'RateLimitBucketItem',
    'RateLimitRuleItem',
    'SchemaDiff',
    'TableMeta',
    'TrackingEventItem',
]
