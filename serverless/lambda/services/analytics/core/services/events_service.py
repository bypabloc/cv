"""Service de la operacion `events`: distribucion, listado y heatmap.

- `distribution`: count + pct por tipo de evento en el rango (cacheada).
- `list`: listado paginado de eventos crudos con filtros (NO cacheado).
- `heatmap`: count por (dia-de-semana, hora) en el rango (cacheada).

`date_to` siempre es EXCLUSIVO (las queries usan `< date_to`); el caller
pasa el limite ya calculado (date_to_exclusive del DateRange).
"""

from __future__ import annotations

from datetime import date
from typing import Any

from services._errors import ServiceError
from shared.cache.decorator import cached
from shared.db.models.taxonomy.event_type import EventType
from shared.db.models.visitor.tracking import TrackingEvent
from shared.db.sa import func, select
from shared.db.session import db_session

_TTL = 60
_NS = 'analytics:events'
_TAGS = ['analytics-aggregate']


@cached(ttl=_TTL, namespace=_NS, tags=_TAGS)
def distribution(*, date_from: date, date_to: date) -> dict[str, Any]:
    """Distribucion de eventos por tipo en el rango (count + pct).

    El `pct` se calcula en Python (no en SQL): Postgres no tiene
    `round(double precision, integer)` y castear a numeric complica la
    expresion del window. El conjunto es chico (1 fila por event_type).
    """
    event_type = func.coalesce(EventType.code_name, '(unknown)')
    try:
        with db_session() as s:
            rows = s.execute(
                select(
                    event_type.label('event_type'),
                    func.count().label('count'),
                )
                .select_from(TrackingEvent)
                .outerjoin(
                    EventType, EventType.id == TrackingEvent.event_type_id
                )
                .where(
                    TrackingEvent.created_at >= date_from,
                    TrackingEvent.created_at < date_to,
                )
                .group_by(EventType.code_name)
                .order_by(func.count().desc())
            ).all()
    except Exception as exc:
        raise ServiceError(f'events distribution query failed: {exc}') from exc

    counts = [(row.event_type, int(row.count or 0)) for row in rows]
    total = sum(c for _, c in counts)
    items = [
        {
            'event_type': name,
            'count': count,
            'pct': round(100.0 * count / total, 2) if total else 0.0,
        }
        for name, count in counts
    ]
    return {'items': items}


def list(
    *,
    date_from: date,
    date_to: date,
    page: int,
    page_size: int,
    offset: int,
    niche: str | None = None,
    event_type: str | None = None,
    session_id: str | None = None,
    page_path: str | None = None,
) -> dict[str, Any]:
    """Listado paginado de eventos crudos del rango (NO cacheado).

    Filtros opcionales: niche, event_type, session_id, page_path. Devuelve
    `{items, page, page_size, total, has_more}` (has_more half-open).
    """
    filters = [
        TrackingEvent.created_at >= date_from,
        TrackingEvent.created_at < date_to,
    ]
    if niche is not None:
        filters.append(TrackingEvent.niche == niche)
    if event_type is not None:
        filters.append(EventType.code_name == event_type)
    if session_id is not None:
        filters.append(TrackingEvent.session_id == session_id)
    if page_path is not None:
        filters.append(TrackingEvent.page_path == page_path)

    try:
        with db_session() as s:
            total = s.scalar(
                select(func.count())
                .select_from(TrackingEvent)
                .outerjoin(
                    EventType, EventType.id == TrackingEvent.event_type_id
                )
                .where(*filters)
            )
            rows = s.execute(
                select(
                    TrackingEvent.created_at,
                    TrackingEvent.visit_id,
                    TrackingEvent.page_id,
                    TrackingEvent.session_id,
                    TrackingEvent.page_path,
                    TrackingEvent.niche,
                    TrackingEvent.viewport_width,
                    TrackingEvent.viewport_height,
                    EventType.code_name.label('event_type'),
                    TrackingEvent.event_props,
                )
                .select_from(TrackingEvent)
                .outerjoin(
                    EventType, EventType.id == TrackingEvent.event_type_id
                )
                .where(*filters)
                .order_by(TrackingEvent.created_at.desc())
                .limit(page_size)
                .offset(offset)
            ).all()
    except Exception as exc:
        raise ServiceError(f'events list query failed: {exc}') from exc

    items = [
        {
            'created_at': (
                row.created_at.isoformat() if row.created_at else None
            ),
            'visit_id': row.visit_id,
            'page_id': row.page_id,
            'session_id': row.session_id,
            'page_path': row.page_path,
            'niche': row.niche,
            'viewport_width': row.viewport_width,
            'viewport_height': row.viewport_height,
            'event_type': row.event_type,
            'event_props': row.event_props,
        }
        for row in rows
    ]
    total = int(total or 0)
    return {
        'items': items,
        'page': page,
        'page_size': page_size,
        'total': total,
        'has_more': (offset + len(items)) < total,
    }


@cached(ttl=_TTL, namespace=_NS, tags=_TAGS)
def heatmap(*, date_from: date, date_to: date) -> dict[str, Any]:
    """Heatmap de eventos por (dia-de-semana ISO, hora) en el rango."""
    dow = func.extract('isodow', TrackingEvent.created_at)
    hour = func.extract('hour', TrackingEvent.created_at)
    try:
        with db_session() as s:
            rows = s.execute(
                select(
                    dow.label('dow'),
                    hour.label('hour'),
                    func.count().label('count'),
                )
                .select_from(TrackingEvent)
                .where(
                    TrackingEvent.created_at >= date_from,
                    TrackingEvent.created_at < date_to,
                )
                .group_by(dow, hour)
                .order_by(dow, hour)
            ).all()
    except Exception as exc:
        raise ServiceError(f'events heatmap query failed: {exc}') from exc

    cells = [
        {
            'dow': int(row.dow),
            'hour': int(row.hour),
            'count': int(row.count or 0),
        }
        for row in rows
    ]
    return {'cells': cells}
