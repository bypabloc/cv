"""@module tracking — `event_types` (catalogo) + `tracking_events`.

Replica en Neon de la tabla DynamoDB `TrackingTable`. El `stream_processor`
inserta una fila por cada evento de tracking que llega via DynamoDB Stream.

Fiel al schema actual (migraciones 001 + 006 + 007 + 008 + 009 +
d4e5f6a7b8c9):
- `tracking_events` esta PARTICIONADA por RANGE(created_at). SQLAlchemy
  declara las columnas; el `PARTITION BY` y la particion default los agrega
  la migracion Alembic con `op.execute()` (Alembic no autogenera
  particionado). El modelo lo anota con `postgresql_partition_by` para que
  el `CREATE TABLE` autogenerado lo incluya.
- PK compuesta `(session_id, page_id)` — debe incluir... ver nota abajo.
- `event_type_id` es FK a `event_types` (PG soporta FK en tabla
  particionada desde PG12).
- `event_props` es JSONB (datos especificos por tipo de evento).
- `session_id` FK a `sessions(session_id)` NOT NULL.
- `visit_id` FK a `session_visits(visit_id)` NOT NULL.
- Spec sessions-normalize dropeo `ip`, `country`, `user_agent`,
  `browser`, `browser_version`, `os`, `device_type`, `utm_*` (todos
  movidos a sessions/session_visits).
"""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class EventType(Base):
    """Catalogo de tipos de evento de tracking.

    Fuente de verdad de los UUID; el frontend los replica como constantes TS
    en build-time (`packages/content`). Por eso el `id` es un UUIDv7 literal
    fijo (sembrado), NO `uuidv7()` en runtime. Seed: 16 tipos.
    """

    __tablename__ = 'event_types'

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    code_name: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class TrackingEvent(Base):
    """Un evento de tracking (replica de DynamoDB, particionada por mes).

    PARTITION BY RANGE(created_at): el `op.execute()` de la migracion crea
    la tabla con la clausula de particionado + la particion default.

    La tabla en prod NO tiene PRIMARY KEY (la migracion 001 nunca la
    declaro; la idempotencia se enforce via `processed_stream_events`). Para
    parity NO se emite ningun PK constraint a la DB. El ORM exige una PK
    para mapear la clase: se declara solo a nivel `mapper`
    (`__mapper_args__.primary_key`), sin constraint fisico.
    """

    __tablename__ = 'tracking_events'

    session_id: Mapped[str] = mapped_column(
        Text, ForeignKey('sessions.session_id'), nullable=False
    )
    visit_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey('session_visits.visit_id'),
        nullable=False,
    )
    page_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Metadata de pagina (la utm/ip/ua/browser de cada evento vive en
    # session_visits + sessions; aqui solo queda page_path por-evento).
    page_path: Mapped[str | None] = mapped_column(Text)

    # Viewport — sigue por-evento (un visit puede rotar mobile/desktop).
    viewport_width: Mapped[int | None] = mapped_column(Integer)
    viewport_height: Mapped[int | None] = mapped_column(Integer)

    # Niche del evento (puede diferir del niche del visit si el usuario
    # navego entre subdominios dentro de la misma visit).
    niche: Mapped[str | None] = mapped_column(Text)

    # Tipo de evento (migracion 007). FK al catalogo.
    event_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    event_type_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey('event_types.id')
    )
    # Datos especificos por tipo de evento (migracion 009).
    event_props: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    # Indices de la migracion 002 + 007 + d4e5f6a7b8c9. Nombres
    # explicitos (idx_*) para parity exacto con el schema de prod. El
    # dict de opciones de tabla (postgresql_partition_by) va SIEMPRE
    # ultimo en __table_args__.
    __table_args__ = (
        # Session journey: WHERE session_id = X ORDER BY created_at.
        Index('idx_tracking_session_created', 'session_id', 'created_at'),
        # BRIN para created_at (time-series con escritura ordenada).
        Index(
            'idx_tracking_created_brin',
            'created_at',
            postgresql_using='brin',
        ),
        Index('idx_tracking_page_path', 'page_path'),
        Index(
            'idx_tracking_niche_created',
            'niche',
            text('created_at DESC'),
            postgresql_where=text('niche IS NOT NULL'),
        ),
        # FK al catalogo event_types (migracion 007).
        Index('idx_tracking_event_type', 'event_type_id'),
        # Spec sessions-normalize: indice del FK visit_id.
        Index('idx_tracking_visit_id', 'visit_id'),
        # Particionado RANGE por mes. La particion default la agrega la
        # migracion con op.execute(). El dict de opciones va ultimo.
        {'postgresql_partition_by': 'RANGE (created_at)'},
    )

    # PK solo a nivel ORM (mapper) — NO emite constraint fisico. La tabla
    # en prod no tiene PK; esto permite mapear la clase sin alterar el
    # schema. `(session_id, page_id, created_at)` identifica una fila.
    __mapper_args__ = {  # noqa: RUF012
        'primary_key': [session_id, page_id, created_at],
    }
