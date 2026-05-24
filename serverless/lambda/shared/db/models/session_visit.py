"""@module session_visit — tabla `session_visits` (visits multi-touch).

Una row por cada combinacion distinta de
`(ip, utm_source, utm_medium, utm_campaign, utm_content, utm_term)`
dentro del mismo `session_id`. Modela el patron multi-touch: un mismo
visitante puede entrar varias veces (twitter, linkedin, directo) con
diferentes UTM o redes — cada cambio = un visit nuevo.

`event_count` es cache denormalizado de `COUNT(*) FROM tracking_events
WHERE visit_id = X`. Se incrementa en la misma tx que el INSERT del
tracking_event/contact (decision 12 del plan sessions-normalize).

Fiel a la migration `d4e5f6a7b8c9`:
- PK natural `visit_id` UUIDv7 server-side (`uuidv7()` PG18).
- FK `session_id` -> `sessions(session_id)` NOT NULL, sin cascade.
- Indices: BRIN started_at, BTree (session_id, started_at DESC),
  parciales en country/niche/utm_source.
"""

from datetime import datetime

from sqlalchemy import CHAR, DateTime, ForeignKey, Index, Integer, Text, func, text
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class SessionVisit(Base):
    """Una visita logica del visitante (cambio de network/utm)."""

    __tablename__ = 'session_visits'

    visit_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=func.uuidv7(),
    )
    session_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey('sessions.session_id'),
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ended_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # Cache denormalizado: COUNT(*) de tracking_events del visit. Se
    # incrementa en la misma tx que el INSERT del tracking_event.
    event_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text('0')
    )

    # Identidad de la visit (snapshot al inicio de cada visit nuevo).
    ip: Mapped[str | None] = mapped_column(INET)
    country: Mapped[str | None] = mapped_column(CHAR(2))

    # Los 6 campos del visit-trigger (cambio en cualquiera -> nuevo visit).
    utm_source: Mapped[str | None] = mapped_column(Text)
    utm_medium: Mapped[str | None] = mapped_column(Text)
    utm_campaign: Mapped[str | None] = mapped_column(Text)
    utm_content: Mapped[str | None] = mapped_column(Text)
    utm_term: Mapped[str | None] = mapped_column(Text)

    referrer: Mapped[str | None] = mapped_column(Text)
    landing_page_path: Mapped[str | None] = mapped_column(Text)
    # niche del landing_page de esta visit. NO cambia aunque el
    # visitante navegue a otro niche dentro de la misma visit
    # (decision 11). tracking_events.niche puede diferir por evento.
    niche: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index(
            'idx_visits_session_started',
            'session_id',
            text('started_at DESC'),
        ),
        Index(
            'idx_visits_started_brin',
            'started_at',
            postgresql_using='brin',
        ),
        Index(
            'idx_visits_country',
            'country',
            postgresql_where=text('country IS NOT NULL'),
        ),
        Index(
            'idx_visits_niche',
            'niche',
            postgresql_where=text('niche IS NOT NULL'),
        ),
        Index(
            'idx_visits_utm_source',
            'utm_source',
            postgresql_where=text('utm_source IS NOT NULL'),
        ),
    )
