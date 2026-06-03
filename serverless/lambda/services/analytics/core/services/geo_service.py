"""Service de la operacion `geo`: distribucion de trafico por pais.

1 funcion publica (`by_country`), agregada -> cacheada 60s. Resuelve
sessions/visits por pais y events por pais en dos queries y las mergea en
Python (mismo resultado que el CTE country_sessions_visits LEFT JOIN
country_events del plan). La convencion de rango es half-open: el caller
pasa `date_to` ya EXCLUSIVO (date_to_exclusive del DateRange); el SQL usa
`< date_to` directo (NUNCA suma 1 dia aca). Eventos: SIEMPRE por
`TrackingEvent.created_at`, nunca `occurred_at`.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from services._errors import ServiceError
from shared.cache.decorator import cached
from shared.db.models.visitor.session_visit import SessionVisit
from shared.db.models.visitor.tracking import TrackingEvent
from shared.db.sa import func, select
from shared.db.session import db_session

_TTL = 60
_NS = 'analytics:geo'
_TAGS = ['analytics-aggregate']


@cached(ttl=_TTL, namespace=_NS, tags=_TAGS)
def by_country(
    *, date_from: date, date_to: date, limit: int = 50
) -> dict[str, Any]:
    """Top paises por sesiones del rango (+ visits + events).

    Pais ausente -> 'XX' (COALESCE). Ordena por sessions desc, LIMIT limit.
    `date_to` es EXCLUSIVO; events se cuentan por `TrackingEvent.created_at`.
    """
    try:
        with db_session() as s:
            country_col = func.coalesce(SessionVisit.country, 'XX')
            sv_rows = s.execute(
                select(
                    country_col.label('country'),
                    func.count(func.distinct(SessionVisit.session_id)).label(
                        'sessions'
                    ),
                    func.count().label('visits'),
                )
                .where(
                    SessionVisit.started_at >= date_from,
                    SessionVisit.started_at < date_to,
                )
                .group_by(country_col)
                .order_by(
                    func.count(func.distinct(SessionVisit.session_id)).desc()
                )
                .limit(limit)
            ).all()

            # session_id -> country (mismo COALESCE) para el join de eventos.
            session_country = {
                row.session_id: row.country
                for row in s.execute(
                    select(
                        SessionVisit.session_id.label('session_id'),
                        country_col.label('country'),
                    )
                    .where(
                        SessionVisit.started_at >= date_from,
                        SessionVisit.started_at < date_to,
                    )
                    .distinct()
                ).all()
            }

            event_rows = s.execute(
                select(
                    TrackingEvent.session_id.label('session_id'),
                    func.count().label('events'),
                )
                .where(
                    TrackingEvent.created_at >= date_from,
                    TrackingEvent.created_at < date_to,
                    TrackingEvent.session_id.in_(session_country.keys()),
                )
                .group_by(TrackingEvent.session_id)
            ).all()
    except Exception as exc:
        raise ServiceError(f'geo by-country query failed: {exc}') from exc

    events_by_country: dict[str, int] = {}
    for row in event_rows:
        country = session_country.get(row.session_id)
        if country is None:
            continue
        events_by_country[country] = events_by_country.get(country, 0) + int(
            row.events or 0
        )

    items: list[dict[str, Any]] = []
    total = 0
    for row in sv_rows:
        sessions = int(row.sessions or 0)
        total += sessions
        items.append(
            {
                'country': row.country,
                'sessions': sessions,
                'visits': int(row.visits or 0),
                'events': events_by_country.get(row.country, 0),
            }
        )
    return {'items': items, 'total': total}
