"""Modelo de la tabla `portfolio-tracking-{stage}` — TEST FIXTURE LEGACY.

Tabla de eventos de tracking pixel. PK compuesta `session_id` (HASH) +
`page_id` (RANGE). TTL 60d via `expires_at`.

GSI `niche-created_at-index` (PK `niche`, SK `created_at`): habilita
queries de dashboard por nicho ordenadas por fecha sin full scan.

**NOTA (spec direct-neon-writes)**: ningun Lambda en produccion importa
esta clase — `tracking_pixel` escribe directo a Neon
(`shared.db.TrackingEvent`) en vez de DynamoDB. La clase se conserva
como fixture para los tests de `shared.dynamodb.BaseModel` (~10 archivos
en `tests/.../shared/dynamodb/` la usan como exemplar concreto).
Cuando esos tests se refactoricen a usar `CacheItem`/
`RateLimitBucketItem` como fixtures unicos, esta clase y la tabla DDB
se pueden eliminar.
"""

from __future__ import annotations

from typing import Any, ClassVar

from shared.dynamodb._schema import GSIMeta, TableMeta
from shared.dynamodb.base import BaseModel


class TrackingEventItem(BaseModel):
    """Un evento de tracking (page view / click) persistido en DynamoDB.

    Los campos opcionales se omiten del Item si estan en `None`.
    `event_props` es un Map de DynamoDB con datos especificos del tipo de
    evento.
    """

    Meta: ClassVar[TableMeta] = TableMeta(
        table_env_var='TRACKING_TABLE_NAME',
        table_ssm_env='SSM_TRACKING_TABLE_PATH',
        table_default='portfolio-tracking-dev',
        partition_key='session_id',
        sort_key='page_id',
        ttl_attr='expires_at',
        gsis=(
            GSIMeta(
                name='niche-created_at-index',
                partition_key='niche',
                sort_key='created_at',
            ),
        ),
    )

    session_id: str
    page_id: str
    created_at: str
    expires_at: int
    page_url: str
    event_id: str
    event_type_id: str
    page_title: str | None = None
    page_path: str | None = None
    referrer: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None
    utm_term: str | None = None
    niche: str | None = None
    viewport_width: int | None = None
    viewport_height: int | None = None
    ip: str | None = None
    country: str | None = None
    user_agent: str | None = None
    browser: str | None = None
    browser_version: str | None = None
    os: str | None = None
    device_type: str | None = None
    event_props: dict[str, Any] | None = None
