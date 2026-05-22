"""Modelo de la tabla `portfolio-rate-limit-rules-{stage}`.

Rules del rate-limit por endpoint / IP / country. PK compuesta
`rule_key` (HASH) + `kind` (RANGE). TTL via `expires_at` (para las rules
de auto-blacklist con expiracion).

Reemplaza el antiguo `TypedDict RateLimitRule` de `rate_limit/rules.py`.
"""

from __future__ import annotations

from typing import Any, ClassVar

from shared.dynamodb._schema import TableMeta
from shared.dynamodb.base import BaseModel


class RateLimitRuleItem(BaseModel):
    """Una rule del rate-limit.

    `kind` discrimina el tipo: `endpoint` | `ip_whitelist` |
    `ip_blacklist` | `country`. `limit`/`window_seconds` aplican a las
    rules de endpoint; `action` a las de block. El filtrado por
    `expires_at` (rule vencida) lo hace `rate_limit/rules.py`, NO el ORM.
    """

    Meta: ClassVar[TableMeta] = TableMeta(
        table_env_var='RATE_LIMIT_RULES_TABLE_NAME',
        table_ssm_env='SSM_RATE_LIMIT_RULES_TABLE_PATH',
        table_default='portfolio-rate-limit-rules-dev',
        partition_key='rule_key',
        sort_key='kind',
        ttl_attr='expires_at',
    )

    rule_key: str
    kind: str
    limit: int | None = None
    window_seconds: int | None = None
    action: str | None = None
    expires_at: int | None = None
    reason: str | None = None
    metadata: dict[str, Any] | None = None
