"""Service de la operacion `visits`: listado paginado y landing pages.

- `list`: listado paginado de visitas crudas con filtros (NO cacheado).
- `landing_pages`: ranking de landing pages por visitas (cacheada).

`date_to` siempre es EXCLUSIVO (las queries usan `< date_to`); el caller
pasa el limite ya calculado (date_to_exclusive del DateRange).
"""

from __future__ import annotations

from datetime import date
from typing import Any

from services._errors import ServiceError
from shared.cache.decorator import cached
from shared.db.models.visitor.session_visit import SessionVisit
from shared.db.sa import func, select
from shared.db.session import db_session

_TTL = 60
_NS = 'analytics:visits'
_TAGS = ['analytics-aggregate']


def list(
    *,
    date_from: date,
    date_to: date,
    page: int,
    page_size: int,
    offset: int,
    niche: str | None = None,
    country: str | None = None,
) -> dict[str, Any]:
    """Listado paginado de visitas crudas del rango (NO cacheado).

    Filtros opcionales: niche, country. Devuelve
    `{items, page, page_size, total, has_more}` (has_more half-open).
    """
    filters = [
        SessionVisit.started_at >= date_from,
        SessionVisit.started_at < date_to,
    ]
    if niche is not None:
        filters.append(SessionVisit.niche == niche)
    if country is not None:
        filters.append(SessionVisit.country == country)

    try:
        with db_session() as s:
            total = s.scalar(
                select(func.count()).select_from(SessionVisit).where(*filters)
            )
            rows = s.execute(
                select(
                    SessionVisit.visit_id,
                    SessionVisit.session_id,
                    SessionVisit.started_at,
                    SessionVisit.ended_at,
                    SessionVisit.event_count,
                    SessionVisit.ip,
                    SessionVisit.country,
                    SessionVisit.utm_source,
                    SessionVisit.utm_medium,
                    SessionVisit.utm_campaign,
                    SessionVisit.referrer,
                    SessionVisit.landing_page_path,
                    SessionVisit.niche,
                )
                .where(*filters)
                .order_by(SessionVisit.started_at.desc())
                .limit(page_size)
                .offset(offset)
            ).all()
    except Exception as exc:
        raise ServiceError(f'visits list query failed: {exc}') from exc

    items = [
        {
            'visit_id': row.visit_id,
            'session_id': row.session_id,
            'started_at': (
                row.started_at.isoformat() if row.started_at else None
            ),
            'ended_at': row.ended_at.isoformat() if row.ended_at else None,
            'event_count': int(row.event_count or 0),
            'ip': str(row.ip) if row.ip is not None else None,
            'country': row.country,
            'utm_source': row.utm_source,
            'utm_medium': row.utm_medium,
            'utm_campaign': row.utm_campaign,
            'referrer': row.referrer,
            'landing_page_path': row.landing_page_path,
            'niche': row.niche,
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
def landing_pages(
    *,
    date_from: date,
    date_to: date,
    limit: int,
) -> dict[str, Any]:
    """Ranking de landing pages por visitas en el rango (cacheada).

    Devuelve `{items:[{landing_page_path, visits, unique_visitors}]}`
    ordenado por visitas desc, limitado a `limit`.
    """
    try:
        with db_session() as s:
            rows = s.execute(
                select(
                    SessionVisit.landing_page_path.label('landing_page_path'),
                    func.count().label('visits'),
                    func.count(func.distinct(SessionVisit.session_id)).label(
                        'unique_visitors'
                    ),
                )
                .where(
                    SessionVisit.started_at >= date_from,
                    SessionVisit.started_at < date_to,
                    SessionVisit.landing_page_path.is_not(None),
                )
                .group_by(SessionVisit.landing_page_path)
                .order_by(func.count().desc())
                .limit(limit)
            ).all()
    except Exception as exc:
        raise ServiceError(f'visits landing_pages query failed: {exc}') from exc

    items = [
        {
            'landing_page_path': row.landing_page_path,
            'visits': int(row.visits or 0),
            'unique_visitors': int(row.unique_visitors or 0),
        }
        for row in rows
    ]
    return {'items': items}
