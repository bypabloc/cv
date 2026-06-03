"""Service de la operacion `analytics`: KPIs y agregaciones del visitante.

7 funciones publicas (una por action). Todas las agregadas van cacheadas
60s (active-now solo 10s con tag 'analytics-live'). Cada funcion envuelve
su query en try/except -> ServiceError. La convencion de rango es half-open:
el caller pasa `date_to` ya EXCLUSIVO (date_to_exclusive del DateRange), el
SQL usa `< date_to` directo (NUNCA suma 1 dia aca).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

from services._errors import ServiceError
from shared.cache.decorator import cached
from shared.db.models.taxonomy.event_type import EventType
from shared.db.models.visitor.contact import Contact
from shared.db.models.visitor.session import Session
from shared.db.models.visitor.session_visit import SessionVisit
from shared.db.models.visitor.tracking import TrackingEvent
from shared.db.sa import func, select
from shared.db.session import db_session

_TTL = 60
_TTL_LIVE = 10
_NS = 'analytics:analytics'
_NS_LIVE = 'analytics:active-now'
_TAGS = ['analytics-aggregate']
_TAGS_LIVE = ['analytics-live']

_ACTIVE_WINDOW_MINUTES = 5
_TIMESERIES_MAX_POINTS = 8784
_UTM_LIMIT = 20


def _rate(numerator: int, denominator: int) -> float:
    """Ratio seguro (0.0 si el denominador es 0), redondeado a 3 decimales."""
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 3)


@cached(ttl=_TTL, namespace=_NS, tags=_TAGS)
def overview(*, date_from: date, date_to: date) -> dict[str, Any]:
    """7 KPIs del rango + el rango (from/to) en isoformat.

    `date_to` es EXCLUSIVO (el caller pasa date_to_exclusive).
    """
    try:
        with db_session() as s:
            sessions = s.scalar(
                select(func.count())
                .select_from(Session)
                .where(
                    Session.first_seen_at >= date_from,
                    Session.first_seen_at < date_to,
                )
            )
            visits = s.scalar(
                select(func.count())
                .select_from(SessionVisit)
                .where(
                    SessionVisit.started_at >= date_from,
                    SessionVisit.started_at < date_to,
                )
            )
            events = s.scalar(
                select(func.count())
                .select_from(TrackingEvent)
                .where(
                    TrackingEvent.created_at >= date_from,
                    TrackingEvent.created_at < date_to,
                )
            )
            contacts = s.scalar(
                select(func.count())
                .select_from(Contact)
                .where(
                    Contact.created_at >= date_from,
                    Contact.created_at < date_to,
                )
            )
            unique_visitors = s.scalar(
                select(
                    func.count(func.distinct(SessionVisit.session_id))
                ).where(
                    SessionVisit.started_at >= date_from,
                    SessionVisit.started_at < date_to,
                )
            )
            avg_duration = s.scalar(
                select(
                    func.coalesce(
                        func.avg(
                            func.extract(
                                'epoch',
                                SessionVisit.ended_at - SessionVisit.started_at,
                            )
                        ),
                        0,
                    )
                ).where(
                    SessionVisit.ended_at.is_not(None),
                    SessionVisit.started_at >= date_from,
                    SessionVisit.started_at < date_to,
                )
            )
            bounce_visits = s.scalar(
                select(func.count())
                .select_from(SessionVisit)
                .where(
                    SessionVisit.event_count == 1,
                    SessionVisit.started_at >= date_from,
                    SessionVisit.started_at < date_to,
                )
            )
    except Exception as exc:
        raise ServiceError(f'overview query failed: {exc}') from exc

    sessions = int(sessions or 0)
    visits = int(visits or 0)
    events = int(events or 0)
    contacts = int(contacts or 0)
    unique_visitors = int(unique_visitors or 0)
    bounce_visits = int(bounce_visits or 0)
    return {
        'sessions': sessions,
        'visits': visits,
        'events': events,
        'contacts': contacts,
        'unique_visitors': unique_visitors,
        'avg_visit_duration_sec': round(float(avg_duration or 0.0), 2),
        'bounce_rate': _rate(bounce_visits, visits),
        'from': date_from.isoformat(),
        'to': date_to.isoformat(),
    }


@cached(ttl=_TTL, namespace=_NS, tags=_TAGS)
def timeseries(
    *,
    date_from: date,
    date_to: date,
    bucket: str = 'day',
    niche: str | None = None,
    event_type: str | None = None,
) -> dict[str, Any]:
    """Serie temporal de eventos agrupada por bucket (day|hour|week).

    Filtra opcionalmente por niche y por event_type (code_name del catalogo
    tax_event_types). `date_to` es EXCLUSIVO.
    """
    try:
        with db_session() as s:
            ts_col = func.date_trunc(bucket, TrackingEvent.created_at)
            stmt = (
                select(ts_col.label('ts'), func.count().label('count'))
                .where(
                    TrackingEvent.created_at >= date_from,
                    TrackingEvent.created_at < date_to,
                )
                .group_by(ts_col)
                .order_by(ts_col.asc())
                .limit(_TIMESERIES_MAX_POINTS)
            )
            if niche is not None:
                stmt = stmt.where(TrackingEvent.niche == niche)
            if event_type is not None:
                stmt = stmt.where(
                    TrackingEvent.event_type_id
                    == select(EventType.id)
                    .where(EventType.code_name == event_type)
                    .scalar_subquery()
                )
            rows = s.execute(stmt).all()
    except Exception as exc:
        raise ServiceError(f'timeseries query failed: {exc}') from exc

    points = [
        {
            'timestamp': row.ts.isoformat() if row.ts is not None else None,
            'count': int(row.count or 0),
        }
        for row in rows
    ]
    return {
        'bucket': bucket,
        'points': points,
        'from': date_from.isoformat(),
        'to': date_to.isoformat(),
        'filters': {'niche': niche, 'event_type': event_type},
    }


@cached(ttl=_TTL, namespace=_NS, tags=_TAGS)
def top_pages(
    *,
    date_from: date,
    date_to: date,
    limit: int = 10,
    niche: str | None = None,
) -> dict[str, Any]:
    """Top page_path por eventos del rango (+ unique_visitors/unique_visits).

    `date_to` es EXCLUSIVO.
    """
    try:
        with db_session() as s:
            stmt = (
                select(
                    TrackingEvent.page_path.label('page_path'),
                    func.count().label('events'),
                    func.count(func.distinct(TrackingEvent.session_id)).label(
                        'unique_visitors'
                    ),
                    func.count(func.distinct(TrackingEvent.visit_id)).label(
                        'unique_visits'
                    ),
                )
                .where(
                    TrackingEvent.created_at >= date_from,
                    TrackingEvent.created_at < date_to,
                    TrackingEvent.page_path.is_not(None),
                )
                .group_by(TrackingEvent.page_path)
                .order_by(func.count().desc())
                .limit(limit)
            )
            if niche is not None:
                stmt = stmt.where(TrackingEvent.niche == niche)
            rows = s.execute(stmt).all()
    except Exception as exc:
        raise ServiceError(f'top-pages query failed: {exc}') from exc

    items = [
        {
            'page_path': row.page_path,
            'events': int(row.events or 0),
            'unique_visitors': int(row.unique_visitors or 0),
            'unique_visits': int(row.unique_visits or 0),
        }
        for row in rows
    ]
    return {'items': items}


def _utm_breakdown(
    s: Any, column: Any, *, date_from: date, date_to: date
) -> list[dict[str, Any]]:
    """Top valores no nulos de una columna utm (count desc, limit 20)."""
    rows = s.execute(
        select(column.label('value'), func.count().label('count'))
        .where(
            SessionVisit.started_at >= date_from,
            SessionVisit.started_at < date_to,
            column.is_not(None),
        )
        .group_by(column)
        .order_by(func.count().desc())
        .limit(_UTM_LIMIT)
    ).all()
    return [{'value': row.value, 'count': int(row.count or 0)} for row in rows]


@cached(ttl=_TTL, namespace=_NS, tags=_TAGS)
def top_referrers(
    *, date_from: date, date_to: date, limit: int = 10
) -> dict[str, Any]:
    """Top referrers + breakdown de utm_source/medium/campaign del rango.

    `date_to` es EXCLUSIVO.
    """
    try:
        with db_session() as s:
            ref_col = func.coalesce(SessionVisit.referrer, '(direct)')
            ref_rows = s.execute(
                select(
                    ref_col.label('referrer'),
                    func.count().label('visits'),
                    func.count(func.distinct(SessionVisit.session_id)).label(
                        'unique_visitors'
                    ),
                )
                .where(
                    SessionVisit.started_at >= date_from,
                    SessionVisit.started_at < date_to,
                )
                .group_by(ref_col)
                .order_by(func.count().desc())
                .limit(limit)
            ).all()
            utm_sources = _utm_breakdown(
                s, SessionVisit.utm_source, date_from=date_from, date_to=date_to
            )
            utm_mediums = _utm_breakdown(
                s, SessionVisit.utm_medium, date_from=date_from, date_to=date_to
            )
            utm_campaigns = _utm_breakdown(
                s,
                SessionVisit.utm_campaign,
                date_from=date_from,
                date_to=date_to,
            )
    except Exception as exc:
        raise ServiceError(f'top-referrers query failed: {exc}') from exc

    referrers = [
        {
            'referrer': row.referrer,
            'visits': int(row.visits or 0),
            'unique_visitors': int(row.unique_visitors or 0),
        }
        for row in ref_rows
    ]
    return {
        'referrers': referrers,
        'utm_sources': utm_sources,
        'utm_mediums': utm_mediums,
        'utm_campaigns': utm_campaigns,
    }


@cached(ttl=_TTL, namespace=_NS, tags=_TAGS)
def top_niches(
    *, date_from: date, date_to: date, limit: int = 10
) -> dict[str, Any]:
    """Top niches por visitas del rango (+ unique_visitors).

    `date_to` es EXCLUSIVO.
    """
    try:
        with db_session() as s:
            niche_col = func.coalesce(SessionVisit.niche, '(none)')
            rows = s.execute(
                select(
                    niche_col.label('niche'),
                    func.count().label('visits'),
                    func.count(func.distinct(SessionVisit.session_id)).label(
                        'unique_visitors'
                    ),
                )
                .where(
                    SessionVisit.started_at >= date_from,
                    SessionVisit.started_at < date_to,
                )
                .group_by(niche_col)
                .order_by(func.count().desc())
                .limit(limit)
            ).all()
    except Exception as exc:
        raise ServiceError(f'top-niches query failed: {exc}') from exc

    items = [
        {
            'niche': row.niche,
            'visits': int(row.visits or 0),
            'unique_visitors': int(row.unique_visitors or 0),
        }
        for row in rows
    ]
    return {'items': items}


@cached(ttl=_TTL_LIVE, namespace=_NS_LIVE, tags=_TAGS_LIVE)
def active_now() -> dict[str, Any]:
    """Sesiones activas (last_seen_at en los ultimos 5 min). TTL cache 10s.

    El threshold se calcula en Python para que la query sea bindeable y el
    campo `as_of` quede determinable en los tests via el threshold.
    """
    now = datetime.now(UTC)
    threshold = now - timedelta(minutes=_ACTIVE_WINDOW_MINUTES)
    try:
        with db_session() as s:
            active = s.scalar(
                select(func.count())
                .select_from(Session)
                .where(Session.last_seen_at >= threshold)
            )
    except Exception as exc:
        raise ServiceError(f'active-now query failed: {exc}') from exc

    return {
        'active_sessions': int(active or 0),
        'threshold_minutes': _ACTIVE_WINDOW_MINUTES,
        'as_of': now.isoformat(),
    }


@cached(ttl=_TTL, namespace=_NS, tags=_TAGS)
def retention(*, date_from: date, date_to: date) -> dict[str, Any]:
    """Visitantes nuevos vs recurrentes del rango + returning_rate.

    Nuevos: sesiones cuyo first_seen_at cae dentro del rango.
    Recurrentes: sesiones que visitaron en el rango pero existian antes
    (first_seen_at < date_from). `date_to` es EXCLUSIVO.
    """
    try:
        with db_session() as s:
            visits_in_range = (
                select(func.distinct(SessionVisit.session_id).label('sid'))
                .where(
                    SessionVisit.started_at >= date_from,
                    SessionVisit.started_at < date_to,
                )
                .subquery()
            )
            row = s.execute(
                select(
                    func.count()
                    .filter(
                        Session.first_seen_at >= date_from,
                        Session.first_seen_at < date_to,
                    )
                    .label('new_visitors'),
                    func.count()
                    .filter(Session.first_seen_at < date_from)
                    .label('returning_visitors'),
                    func.count().label('total'),
                ).select_from(
                    visits_in_range.join(
                        Session,
                        Session.session_id == visits_in_range.c.sid,
                    )
                )
            ).one()
    except Exception as exc:
        raise ServiceError(f'retention query failed: {exc}') from exc

    new_visitors = int(row.new_visitors or 0)
    returning_visitors = int(row.returning_visitors or 0)
    total = int(row.total or 0)
    return {
        'new_visitors': new_visitors,
        'returning_visitors': returning_visitors,
        'total': total,
        'returning_rate': _rate(returning_visitors, total),
    }
