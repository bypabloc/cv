"""Modelo de la tabla `portfolio-contacts-{stage}` — TEST FIXTURE LEGACY.

Tabla del form de contacto. PK simple `id` (UUIDv7); `created_at` es un
atributo, NO sort key (paridad con `infra.yaml`).

**NOTA (spec direct-neon-writes)**: ningun Lambda en produccion importa
esta clase — `contact_form` escribe directo a Neon (`shared.db.Contact`)
en vez de DynamoDB. La clase se conserva como fixture para los tests de
`shared.dynamodb.BaseModel` (~10 archivos en `tests/.../shared/dynamodb/`
la usan como exemplar concreto). Cuando esos tests se refactoricen a usar
`CacheItem`/`RateLimitBucketItem` como fixtures unicos, esta clase y la
tabla DDB se pueden eliminar.
"""

from __future__ import annotations

from typing import ClassVar

from shared.dynamodb._schema import TableMeta
from shared.dynamodb.base import BaseModel


class ContactItem(BaseModel):
    """Un contact submission persistido en DynamoDB.

    Los campos opcionales (`company`..`session_id`) se omiten del Item si
    estan en `None` (lo hace `BaseModel.to_item`). `session_id` enlaza el
    contacto con `tracking_events` via JOIN en Neon.
    """

    Meta: ClassVar[TableMeta] = TableMeta(
        table_env_var='CONTACTS_TABLE_NAME',
        table_ssm_env='SSM_CONTACTS_TABLE_PATH',
        table_default='portfolio-contacts-dev',
        partition_key='id',
    )

    id: str
    created_at: str
    name: str
    email: str
    message: str
    company: str | None = None
    role: str | None = None
    service_type: str | None = None
    budget: str | None = None
    timeline: str | None = None
    niche: str | None = None
    session_id: str | None = None
