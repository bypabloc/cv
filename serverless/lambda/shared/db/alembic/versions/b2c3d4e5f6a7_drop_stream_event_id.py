"""drop stream_event_id + add cloudfront_meta to tracking_events and contacts

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-24 16:00:00.000000

Spec tracking-data-completeness:

1. DROP `stream_event_id`: columna legacy del flujo
   `Lambda -> DDB -> Stream -> stream_processor -> Neon`. Tras
   direct-neon-writes (mayo 2026) los Lambdas HTTP escriben directo a
   Neon y la columna queda huerfana (sin consumer en codigo vivo).
2. ADD `cloudfront_meta` JSONB: contenedor para TODOS los headers
   `cloudfront-*` que llegan al Lambda cuando el custom domain es
   Edge-Optimized (commits 2-4 de este plan). Captura completa para
   analitica futura: viewer-country/region/city/postal/lat/long/metro/
   time-zone/address/asn/ja3-fingerprint/tls/http-version + device
   flags. `country` (CHAR(2)) sigue siendo la columna tipada de
   conveniencia para queries.

Tablas afectadas: tracking_events (particionada) y contacts.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Drop stream_event_id + add cloudfront_meta a las 2 tablas."""
    # contacts ----------------------------------------------------------
    op.drop_constraint(
        op.f('uq_contacts_stream_event_id'),
        'contacts',
        type_='unique',
    )
    op.drop_column('contacts', 'stream_event_id')
    op.add_column(
        'contacts',
        sa.Column('cloudfront_meta', JSONB(), nullable=True),
    )

    # tracking_events (particionada) ------------------------------------
    # En PG particionadas, drop_column propaga a particiones automatica-
    # mente (PG14+). Igual con add_column.
    op.drop_column('tracking_events', 'stream_event_id')
    op.add_column(
        'tracking_events',
        sa.Column('cloudfront_meta', JSONB(), nullable=True),
    )


def downgrade() -> None:
    """Recrea stream_event_id + drop cloudfront_meta."""
    # tracking_events
    op.drop_column('tracking_events', 'cloudfront_meta')
    op.add_column(
        'tracking_events',
        sa.Column('stream_event_id', sa.Text(), nullable=True),
    )

    # contacts
    op.drop_column('contacts', 'cloudfront_meta')
    op.add_column(
        'contacts',
        sa.Column('stream_event_id', sa.Text(), nullable=True),
    )
    op.create_unique_constraint(
        op.f('uq_contacts_stream_event_id'),
        'contacts',
        ['stream_event_id'],
    )
