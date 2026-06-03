"""Service de la operacion `devices`.

Calcula 3 distribuciones de los visitantes a partir de `vis_sessions`:
`device_types`, `browsers` (top 20) y `os` (top 20), cada lista ordenada
descendente por numero de sesiones. Resultado cacheado (AC-14).
"""

from __future__ import annotations

from datetime import date
from typing import Any

from services._errors import ServiceError
from shared.cache.decorator import cached
from shared.db.models.visitor.session import Session
from shared.db.sa import func, select
from shared.db.session import db_session

_TTL = 60
_NS = 'analytics:devices'
_TAGS = ['analytics-aggregate']
_TOP_LIMIT = 20
_UNKNOWN = '(unknown)'


def _distribution(
    *,
    session: Any,
    column: Any,
    key: str,
    date_from: date,
    date_to: date,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Agrega `count(*)` agrupando por `column`, ordenado desc por sesiones."""
    label = func.coalesce(column, _UNKNOWN)
    stmt = (
        select(label.label(key), func.count().label('sessions'))
        .select_from(Session)
        .where(
            Session.first_seen_at >= date_from,
            Session.first_seen_at < date_to,
        )
        .group_by(column)
        .order_by(func.count().desc())
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    rows = session.execute(stmt).all()
    return [
        {key: getattr(row, key), 'sessions': int(row.sessions or 0)}
        for row in rows
    ]


@cached(ttl=_TTL, namespace=_NS, tags=_TAGS)
def breakdown(*, date_from: date, date_to: date) -> dict[str, Any]:
    """Devuelve device_types, browsers (top 20) y os (top 20)."""
    try:
        with db_session() as s:
            device_types = _distribution(
                session=s,
                column=Session.device_type,
                key='device_type',
                date_from=date_from,
                date_to=date_to,
            )
            browsers = _distribution(
                session=s,
                column=Session.browser,
                key='browser',
                date_from=date_from,
                date_to=date_to,
                limit=_TOP_LIMIT,
            )
            os_dist = _distribution(
                session=s,
                column=Session.os,
                key='os',
                date_from=date_from,
                date_to=date_to,
                limit=_TOP_LIMIT,
            )
    except Exception as exc:
        raise ServiceError(f'devices query failed: {exc}') from exc
    return {
        'device_types': device_types,
        'browsers': browsers,
        'os': os_dist,
    }
