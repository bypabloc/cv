"""Service de la operacion `funnel`: embudo session -> visit -> contact.

Query agregada (3 counts en el rango) -> cacheada 60s. Los rates se
calculan en Python para manejar la division por cero.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from services._errors import ServiceError
from shared.cache.decorator import cached
from shared.db.models.visitor.contact import Contact
from shared.db.models.visitor.session import Session
from shared.db.models.visitor.session_visit import SessionVisit
from shared.db.sa import func, select
from shared.db.session import db_session

_TTL = 60
_NS = 'analytics:funnel'
_TAGS = ['analytics-aggregate']


def _rate(numerator: int, denominator: int) -> float:
    """Ratio seguro (0.0 si el denominador es 0), redondeado a 3 decimales."""
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 3)


@cached(ttl=_TTL, namespace=_NS, tags=_TAGS)
def conversion(*, date_from: date, date_to: date) -> dict[str, Any]:
    """Devuelve sessions/visits/contacts del rango + 3 rates de conversion.

    `date_to` es EXCLUSIVO (las queries usan `< date_to`); el caller pasa
    el limite ya calculado (date_to_exclusive del DateRange).
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
                select(
                    func.count(func.distinct(SessionVisit.session_id))
                ).where(
                    SessionVisit.started_at >= date_from,
                    SessionVisit.started_at < date_to,
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
    except Exception as exc:
        raise ServiceError(f'funnel query failed: {exc}') from exc

    sessions = int(sessions or 0)
    visits = int(visits or 0)
    contacts = int(contacts or 0)
    return {
        'sessions': sessions,
        'visits': visits,
        'contacts': contacts,
        'session_to_visit_rate': _rate(visits, sessions),
        'visit_to_contact_rate': _rate(contacts, visits),
        'session_to_contact_rate': _rate(contacts, sessions),
    }
