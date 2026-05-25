"""Modelo de la tabla `portfolio-rate-limit-buckets-{stage}`.

Buckets del sliding window weighted del rate-limit. PK simple
`bucket_key`. TTL via `expires_at`. Los contadores `count` y
`turnstile_tokens` se actualizan con `increment()` (operacion `ADD`
atomica), no con `save()`.
"""

from __future__ import annotations

from typing import ClassVar

from shared.dynamodb._schema import TableMeta
from shared.dynamodb.base import BaseModel


class RateLimitBucketItem(BaseModel):
    """Un bucket de conteo del rate-limit (una ventana ip+endpoint).

    `count` cuenta requests; `turnstile_tokens` cuenta tokens Turnstile
    validos en la ventana (para el auto-blacklist). Ambos default 0: un
    bucket recien leido sin item devuelve ceros.
    """

    Meta: ClassVar[TableMeta] = TableMeta(
        table_env_var='RATE_LIMIT_BUCKETS_TABLE_NAME',
        table_ssm_env='SSM_RATE_LIMIT_BUCKETS_TABLE_PATH',
        table_default='portfolio-rate-limit-buckets-dev',
        partition_key='bucket_key',
        ttl_attr='expires_at',
    )

    bucket_key: str
    count: int = 0
    turnstile_tokens: int = 0
    expires_at: int | None = None
