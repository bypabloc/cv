"""drop processed_stream_events table

Revision ID: a1b2c3d4e5f6
Revises: 7c4d9e1b2a3f
Create Date: 2026-05-24 14:00:00.000000

Spec direct-neon-writes: el stream_processor se elimino (los Lambdas
HTTP escriben directo a Neon). La tabla `processed_stream_events`
servia para idempotencia del Stream — ya no tiene consumer.

La tabla se conserva vacia historicamente; el `op.drop_table` la
elimina del schema. El `downgrade()` la recrea para permitir rollback
operativo (no se va a usar, pero mantiene la cadena de revisiones
reversible).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '7c4d9e1b2a3f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Drop la tabla `processed_stream_events`.

    La tabla esta vacia (el stream_processor se elimino antes de esta
    migracion). DROP no requiere CASCADE: no hay FKs apuntando a ella.
    """
    op.drop_table('processed_stream_events')


def downgrade() -> None:
    """Recrea la tabla con el schema original (migracion 001).

    Definicion exacta del init unified schema (`81c2cc51db34`): event_id
    TEXT PK, processed_at TIMESTAMPTZ default now(), event_type TEXT,
    table_name TEXT. Sin indices adicionales — la PK basta.
    """
    op.create_table(
        'processed_stream_events',
        sa.Column('event_id', sa.Text(), nullable=False),
        sa.Column(
            'processed_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('event_type', sa.Text(), nullable=True),
        sa.Column('table_name', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint(
            'event_id', name=op.f('pk_processed_stream_events')
        ),
    )
