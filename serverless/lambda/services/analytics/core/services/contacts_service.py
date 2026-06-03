"""Service de la operacion `contacts`: listado paginado y distribucion.

- `list`: listado paginado de contactos crudos con filtros status/niche
  (PII, NO cacheado). `id` es UUID -> se emite como `str`.
- `by_status`: count + pct por status en el rango (agregada -> cacheada).

`date_to` siempre es EXCLUSIVO (las queries usan `< date_to`); el caller
pasa el limite ya calculado (date_to_exclusive del DateRange). NUNCA se
suma 1 dia en el SQL.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from services._errors import ServiceError
from shared.cache.decorator import cached
from shared.db.models.visitor.contact import Contact
from shared.db.sa import func, select
from shared.db.session import db_session

_TTL = 60
_NS = 'analytics:contacts'
_TAGS = ['analytics-aggregate']


def list(
    *,
    date_from: date,
    date_to: date,
    page: int,
    page_size: int,
    offset: int,
    status: str | None = None,
    niche: str | None = None,
) -> dict[str, Any]:
    """Listado paginado de contactos crudos del rango (NO cacheado, PII).

    Filtros opcionales: status, niche. Devuelve
    `{items, page, page_size, total, has_more}` (has_more half-open). El `id`
    (UUID) se emite como `str` para ser JSON-serializable.
    """
    filters = [
        Contact.created_at >= date_from,
        Contact.created_at < date_to,
    ]
    if status is not None:
        filters.append(Contact.status == status)
    if niche is not None:
        filters.append(Contact.niche == niche)

    try:
        with db_session() as s:
            total = s.scalar(
                select(func.count()).select_from(Contact).where(*filters)
            )
            rows = s.execute(
                select(
                    Contact.id,
                    Contact.created_at,
                    Contact.name,
                    Contact.email,
                    Contact.message,
                    Contact.company,
                    Contact.role,
                    Contact.service_type,
                    Contact.budget,
                    Contact.timeline,
                    Contact.niche,
                    Contact.status,
                    Contact.session_id,
                )
                .where(*filters)
                .order_by(Contact.created_at.desc())
                .limit(page_size)
                .offset(offset)
            ).all()
    except Exception as exc:
        raise ServiceError(f'contacts list query failed: {exc}') from exc

    items = [
        {
            'id': str(row.id),
            'created_at': (
                row.created_at.isoformat() if row.created_at else None
            ),
            'name': row.name,
            'email': row.email,
            'message': row.message,
            'company': row.company,
            'role': row.role,
            'service_type': row.service_type,
            'budget': row.budget,
            'timeline': row.timeline,
            'niche': row.niche,
            'status': row.status,
            'session_id': row.session_id,
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
def by_status(*, date_from: date, date_to: date) -> dict[str, Any]:
    """Distribucion de contactos por status en el rango (count + pct).

    El `pct` se calcula en Python (Postgres no tiene `round(double
    precision, integer)`). El conjunto es chico (1 fila por status).
    """
    try:
        with db_session() as s:
            rows = s.execute(
                select(
                    Contact.status.label('status'),
                    func.count().label('count'),
                )
                .select_from(Contact)
                .where(
                    Contact.created_at >= date_from,
                    Contact.created_at < date_to,
                )
                .group_by(Contact.status)
                .order_by(func.count().desc())
            ).all()
    except Exception as exc:
        raise ServiceError(f'contacts by-status query failed: {exc}') from exc

    counts = [(row.status, int(row.count or 0)) for row in rows]
    total = sum(c for _, c in counts)
    items = [
        {
            'status': status,
            'count': count,
            'pct': round(100.0 * count / total, 2) if total else 0.0,
        }
        for status, count in counts
    ]
    return {'items': items}
