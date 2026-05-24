"""ORM minimalista para DynamoDB del backend serverless del portfolio.

Cada tabla del backend se modela como una subclase de `BaseModel`
(Pydantic) con un `Meta: TableMeta`. El `BaseModel` encapsula todo el
acceso boto3, reusa el resource singleton de `shared.dynamodb_client`,
convierte `Decimal` de forma transparente y expone DML (datos) + DDL
acotado (verificacion de esquema + create solo para tests/local).

Las tablas reales de dev/stage/prod las sigue creando devtools con
`aws dynamodb create-table`, leyendo el catalogo de
`serverless/lambda/resources/dynamodb/*.yaml` (3 tablas: `cache`,
`rate-limit-rules`, `rate-limit-buckets`). Ver `README.md` de este
paquete.

Modelos en uso (produccion):

    from shared.dynamodb import CacheItem, RateLimitBucketItem

Modelos legacy (TEST FIXTURES — spec direct-neon-writes):

    ContactItem, TrackingEventItem ya no se importan en codigo de
    produccion (`contact_form`/`tracking_pixel` escriben directo a Neon).
    Se conservan como exemplars de `BaseModel` para los tests de
    `shared.dynamodb`. Si se refactorizan esos tests, las clases pueden
    eliminarse — ver docstring en `models/{contact,tracking}.py`.
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
