"""Service de la operacion `sessions`.

- `list`: listado paginado de sesiones (NO cacheado). Filtros opcionales
  device_type/browser. Devuelve {items, page, page_size, total, has_more}.
- `detail`: detalle de UNA sesion (NO cacheado, NO paginado). 3 queries
  (sesion + visitas + count de eventos). Levanta NotFoundError si la
  sesion no existe (AC-11).

Ningun listado crudo lleva @cached.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from services._errors import NotFoundError, ServiceError
from shared.db.models.visitor.session import Session
from shared.db.models.visitor.session_visit import SessionVisit
from shared.db.models.visitor.tracking import TrackingEvent
from shared.db.sa import func, select
from shared.db.session import db_session


def _iso(value: Any) -> str | None:
    """ISO 8601 del datetime, o None si es None (JSON-serializable)."""
    return value.isoformat() if value is not None else None


def list(
    *,
    date_from: date,
    date_to: date,
    page: int,
    page_size: int,
    offset: int,
    device_type: str | None = None,
    browser: str | None = None,
) -> dict[str, Any]:
    """Listado paginado de sesiones del rango, con filtros opcionales.

    `date_to` es EXCLUSIVO (las queries usan `< date_to`); el caller pasa
    el limite ya calculado (date_to_exclusive del DateRange). Devuelve
    {items, page, page_size, total, has_more}.
    """
    try:
        with db_session() as s:
            filters = [
                Session.first_seen_at >= date_from,
                Session.first_seen_at < date_to,
            ]
            if device_type is not None:
                filters.append(Session.device_type == device_type)
            if browser is not None:
                filters.append(Session.browser == browser)

            total = s.scalar(
                select(func.count()).select_from(Session).where(*filters)
            )

            rows = s.execute(
                select(
                    Session.session_id,
                    Session.first_seen_at,
                    Session.last_seen_at,
                    Session.browser,
                    Session.browser_version,
                    Session.os,
                    Session.device_type,
                    func.count(SessionVisit.visit_id).label('visits_count'),
                )
                .select_from(Session)
                .join(
                    SessionVisit,
                    (SessionVisit.session_id == Session.session_id)
                    & (SessionVisit.started_at >= date_from)
                    & (SessionVisit.started_at < date_to),
                    isouter=True,
                )
                .where(*filters)
                .group_by(Session.session_id)
                .order_by(Session.last_seen_at.desc())
                .limit(page_size)
                .offset(offset)
            ).all()
    except Exception as exc:
        raise ServiceError(f'sessions list query failed: {exc}') from exc

    total = int(total or 0)
    items = [
        {
            'session_id': r.session_id,
            'first_seen_at': _iso(r.first_seen_at),
            'last_seen_at': _iso(r.last_seen_at),
            'browser': r.browser,
            'browser_version': r.browser_version,
            'os': r.os,
            'device_type': r.device_type,
            'visits_count': int(r.visits_count or 0),
        }
        for r in rows
    ]
    return {
        'items': items,
        'page': page,
        'page_size': page_size,
        'total': total,
        'has_more': offset + len(items) < total,
    }


def detail(*, session_id: str) -> dict[str, Any]:
    """Detalle de UNA sesion: datos + visitas + count de eventos.

    Levanta NotFoundError (code 4040) si la sesion no existe (AC-11). El
    shape de salida es {session, visits, events_count} (AC-12).
    """
    try:
        with db_session() as s:
            session_row = s.execute(
                select(
                    Session.session_id,
                    Session.first_seen_at,
                    Session.last_seen_at,
                    Session.browser,
                    Session.browser_version,
                    Session.os,
                    Session.device_type,
                ).where(Session.session_id == session_id)
            ).first()

            if session_row is None:
                raise NotFoundError(f'session {session_id} not found')

            visit_rows = s.execute(
                select(
                    SessionVisit.visit_id,
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
                .where(SessionVisit.session_id == session_id)
                .order_by(SessionVisit.started_at.asc())
            ).all()

            events_count = s.scalar(
                select(func.count())
                .select_from(TrackingEvent)
                .where(TrackingEvent.session_id == session_id)
            )
    except NotFoundError:
        raise
    except Exception as exc:
        raise ServiceError(f'sessions detail query failed: {exc}') from exc

    session = {
        'session_id': session_row.session_id,
        'first_seen_at': _iso(session_row.first_seen_at),
        'last_seen_at': _iso(session_row.last_seen_at),
        'browser': session_row.browser,
        'browser_version': session_row.browser_version,
        'os': session_row.os,
        'device_type': session_row.device_type,
    }
    visits = [
        {
            'visit_id': v.visit_id,
            'started_at': _iso(v.started_at),
            'ended_at': _iso(v.ended_at),
            'event_count': int(v.event_count or 0),
            'ip': str(v.ip) if v.ip is not None else None,
            'country': v.country,
            'utm_source': v.utm_source,
            'utm_medium': v.utm_medium,
            'utm_campaign': v.utm_campaign,
            'referrer': v.referrer,
            'landing_page_path': v.landing_page_path,
            'niche': v.niche,
        }
        for v in visit_rows
    ]
    return {
        'session': session,
        'visits': visits,
        'events_count': int(events_count or 0),
    }
