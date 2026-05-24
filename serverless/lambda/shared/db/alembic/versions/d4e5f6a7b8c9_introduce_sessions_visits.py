"""introduce sessions + session_visits, FK desde tracking_events y contacts

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-24 23:00:00.000000

Spec sessions-normalize:

Refactor del schema para eliminar la duplicacion de
session_id/ip/country/user_agent/utm_*/browser/os/device_type entre
`tracking_events` y `contacts`. Introduce 2 tablas nuevas:

- `sessions` (identidad estable del visitante): session_id PK,
  first_seen_at, last_seen_at, user_agent, browser, browser_version,
  os, device_type.
- `session_visits` (cada cambio de network/utm): visit_id PK (UUIDv7
  server-side), session_id FK, started_at, ended_at, event_count
  (cache denormalizado), ip, country, utm_*, referrer,
  landing_page_path, niche.

`tracking_events` pierde: ip, country, user_agent, browser,
browser_version, os, device_type, utm_source, utm_medium, utm_campaign,
utm_content, utm_term. Agrega visit_id (UUID NOT NULL) + FKs a
sessions(session_id) y session_visits(visit_id).

`contacts` pierde: ip, country, user_agent. Cambia session_id de
nullable a NOT NULL + FK a sessions(session_id).

Decision 3 del plan: TRUNCATE en TODOS los stages — no se consolida la
data historica. La migracion es destructiva en dev/stage/prod por
diseno (los datos son de smoke testing).

`downgrade()` invierte: ADD COLUMNs (todas nullable), DROP FKs,
DROP TABLE session_visits, DROP TABLE sessions. Las columnas vuelven a
existir pero sin la data perdida (no se preservan al subir).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import CHAR, INET, UUID


# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Crea sessions + session_visits, drop columnas redundantes, FKs."""
    # 1. TRUNCATE: borra rows previos (decision 3 del plan). Hace falta
    #    para luego setear session_id/visit_id como NOT NULL sin valor
    #    default.
    op.execute('TRUNCATE TABLE tracking_events CASCADE')
    op.execute('TRUNCATE TABLE contacts CASCADE')

    # 2. CREATE TABLE sessions ------------------------------------------
    op.create_table(
        'sessions',
        sa.Column('session_id', sa.Text(), primary_key=True),
        sa.Column(
            'first_seen_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            'last_seen_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('browser', sa.Text(), nullable=True),
        sa.Column('browser_version', sa.Text(), nullable=True),
        sa.Column('os', sa.Text(), nullable=True),
        sa.Column('device_type', sa.Text(), nullable=True),
    )
    op.create_index(
        'idx_sessions_first_seen_brin',
        'sessions',
        ['first_seen_at'],
        postgresql_using='brin',
    )
    op.create_index(
        'idx_sessions_last_seen',
        'sessions',
        [sa.text('last_seen_at DESC')],
    )

    # 3. CREATE TABLE session_visits ------------------------------------
    op.create_table(
        'session_visits',
        sa.Column(
            'visit_id',
            UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.func.uuidv7(),
        ),
        sa.Column(
            'session_id',
            sa.Text(),
            sa.ForeignKey('sessions.session_id'),
            nullable=False,
        ),
        sa.Column(
            'started_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            'ended_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        # Cache denormalizado: COUNT(*) de tracking_events del visit.
        # Cada INSERT en tracking_events suma 1 en la misma tx (AC-15/16).
        sa.Column(
            'event_count',
            sa.Integer(),
            nullable=False,
            server_default=sa.text('0'),
        ),
        sa.Column('ip', INET(), nullable=True),
        sa.Column('country', CHAR(2), nullable=True),
        # 6 campos del visit-trigger (cambio en cualquiera -> nuevo visit):
        sa.Column('utm_source', sa.Text(), nullable=True),
        sa.Column('utm_medium', sa.Text(), nullable=True),
        sa.Column('utm_campaign', sa.Text(), nullable=True),
        sa.Column('utm_content', sa.Text(), nullable=True),
        sa.Column('utm_term', sa.Text(), nullable=True),
        sa.Column('referrer', sa.Text(), nullable=True),
        sa.Column('landing_page_path', sa.Text(), nullable=True),
        sa.Column('niche', sa.Text(), nullable=True),
    )
    op.create_index(
        'idx_visits_session_started',
        'session_visits',
        ['session_id', sa.text('started_at DESC')],
    )
    op.create_index(
        'idx_visits_started_brin',
        'session_visits',
        ['started_at'],
        postgresql_using='brin',
    )
    op.create_index(
        'idx_visits_country',
        'session_visits',
        ['country'],
        postgresql_where=sa.text('country IS NOT NULL'),
    )
    op.create_index(
        'idx_visits_niche',
        'session_visits',
        ['niche'],
        postgresql_where=sa.text('niche IS NOT NULL'),
    )
    op.create_index(
        'idx_visits_utm_source',
        'session_visits',
        ['utm_source'],
        postgresql_where=sa.text('utm_source IS NOT NULL'),
    )

    # 4. tracking_events: drop columnas movidas a sessions/visits -------
    # En PG14+ DROP COLUMN propaga a particiones automaticamente.
    op.drop_index('idx_tracking_utm_source', table_name='tracking_events')
    op.drop_index('idx_tracking_country', table_name='tracking_events')
    op.drop_index('idx_tracking_device_type', table_name='tracking_events')
    op.drop_column('tracking_events', 'utm_source')
    op.drop_column('tracking_events', 'utm_medium')
    op.drop_column('tracking_events', 'utm_campaign')
    op.drop_column('tracking_events', 'utm_content')
    op.drop_column('tracking_events', 'utm_term')
    op.drop_column('tracking_events', 'ip')
    op.drop_column('tracking_events', 'country')
    op.drop_column('tracking_events', 'user_agent')
    op.drop_column('tracking_events', 'browser')
    op.drop_column('tracking_events', 'browser_version')
    op.drop_column('tracking_events', 'os')
    op.drop_column('tracking_events', 'device_type')

    # 5. tracking_events: agregar visit_id + FKs --------------------------
    op.add_column(
        'tracking_events',
        sa.Column('visit_id', UUID(as_uuid=False), nullable=True),
    )
    # Post-TRUNCATE no hay rows -> ALTER NOT NULL es seguro.
    op.alter_column('tracking_events', 'visit_id', nullable=False)
    op.alter_column('tracking_events', 'session_id', nullable=False)
    op.create_foreign_key(
        'fk_tracking_events_session',
        'tracking_events',
        'sessions',
        ['session_id'],
        ['session_id'],
    )
    op.create_foreign_key(
        'fk_tracking_events_visit',
        'tracking_events',
        'session_visits',
        ['visit_id'],
        ['visit_id'],
    )
    op.create_index(
        'idx_tracking_visit_id', 'tracking_events', ['visit_id']
    )

    # 6. contacts: drop columnas movidas + ALTER session_id + FK ---------
    op.drop_column('contacts', 'ip')
    op.drop_column('contacts', 'country')
    op.drop_column('contacts', 'user_agent')
    # Post-TRUNCATE no hay rows -> ALTER NOT NULL es seguro.
    op.alter_column('contacts', 'session_id', nullable=False)
    op.create_foreign_key(
        'fk_contacts_session',
        'contacts',
        'sessions',
        ['session_id'],
        ['session_id'],
    )
    # El indice viejo era parcial WHERE session_id IS NOT NULL; ahora
    # session_id es NOT NULL, el indice parcial es redundante.
    op.drop_index('idx_contacts_session_id', table_name='contacts')
    op.create_index('idx_contacts_session_id', 'contacts', ['session_id'])


def downgrade() -> None:
    """Recrea columnas (nullable), drop FKs, drop sessions/session_visits.

    NOTA: no se preserva data — el upgrade hizo TRUNCATE y el downgrade
    no puede reconstruirla. Las columnas vuelven a existir vacias.
    """
    # 6. contacts: revertir -------------------------------------------
    op.drop_index('idx_contacts_session_id', table_name='contacts')
    op.create_index(
        'idx_contacts_session_id',
        'contacts',
        ['session_id'],
        postgresql_where=sa.text('session_id IS NOT NULL'),
    )
    op.drop_constraint('fk_contacts_session', 'contacts', type_='foreignkey')
    op.alter_column('contacts', 'session_id', nullable=True)
    op.add_column(
        'contacts', sa.Column('user_agent', sa.Text(), nullable=True),
    )
    op.add_column(
        'contacts', sa.Column('country', CHAR(2), nullable=True),
    )
    op.add_column(
        'contacts', sa.Column('ip', INET(), nullable=True),
    )

    # 5/4. tracking_events: revertir ----------------------------------
    op.drop_index('idx_tracking_visit_id', table_name='tracking_events')
    op.drop_constraint(
        'fk_tracking_events_visit', 'tracking_events', type_='foreignkey',
    )
    op.drop_constraint(
        'fk_tracking_events_session', 'tracking_events',
        type_='foreignkey',
    )
    op.alter_column('tracking_events', 'session_id', nullable=True)
    op.drop_column('tracking_events', 'visit_id')

    # ADD COLUMNs en el orden inverso al drop original.
    op.add_column(
        'tracking_events',
        sa.Column('device_type', sa.Text(), nullable=True),
    )
    op.add_column(
        'tracking_events',
        sa.Column('os', sa.Text(), nullable=True),
    )
    op.add_column(
        'tracking_events',
        sa.Column('browser_version', sa.Text(), nullable=True),
    )
    op.add_column(
        'tracking_events',
        sa.Column('browser', sa.Text(), nullable=True),
    )
    op.add_column(
        'tracking_events',
        sa.Column('user_agent', sa.Text(), nullable=True),
    )
    op.add_column(
        'tracking_events',
        sa.Column('country', CHAR(2), nullable=True),
    )
    op.add_column(
        'tracking_events',
        sa.Column('ip', INET(), nullable=True),
    )
    op.add_column(
        'tracking_events',
        sa.Column('utm_term', sa.Text(), nullable=True),
    )
    op.add_column(
        'tracking_events',
        sa.Column('utm_content', sa.Text(), nullable=True),
    )
    op.add_column(
        'tracking_events',
        sa.Column('utm_campaign', sa.Text(), nullable=True),
    )
    op.add_column(
        'tracking_events',
        sa.Column('utm_medium', sa.Text(), nullable=True),
    )
    op.add_column(
        'tracking_events',
        sa.Column('utm_source', sa.Text(), nullable=True),
    )
    # Recrear indices dropeados en upgrade
    op.create_index(
        'idx_tracking_device_type', 'tracking_events', ['device_type'],
    )
    op.create_index(
        'idx_tracking_country',
        'tracking_events',
        ['country'],
        postgresql_where=sa.text('country IS NOT NULL'),
    )
    op.create_index(
        'idx_tracking_utm_source',
        'tracking_events',
        ['utm_source'],
        postgresql_where=sa.text('utm_source IS NOT NULL'),
    )

    # 3/2. DROP TABLE session_visits + sessions -----------------------
    op.drop_index('idx_visits_utm_source', table_name='session_visits')
    op.drop_index('idx_visits_niche', table_name='session_visits')
    op.drop_index('idx_visits_country', table_name='session_visits')
    op.drop_index('idx_visits_started_brin', table_name='session_visits')
    op.drop_index('idx_visits_session_started', table_name='session_visits')
    op.drop_table('session_visits')

    op.drop_index('idx_sessions_last_seen', table_name='sessions')
    op.drop_index('idx_sessions_first_seen_brin', table_name='sessions')
    op.drop_table('sessions')
