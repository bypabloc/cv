"""Modelo de la tabla `portfolio-contacts-{stage}`.

Tabla del form de contacto. PK simple `id` (UUIDv7); `created_at` es un
atributo, NO sort key (paridad con `infra.yaml`).
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
