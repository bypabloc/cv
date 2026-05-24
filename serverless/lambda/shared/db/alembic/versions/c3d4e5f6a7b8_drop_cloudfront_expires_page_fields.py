"""drop columnas huerfanas y idx_tracking_referrer

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-24 22:00:00.000000

Spec drop-cloudfront-meta:

Drop forward de 6 columnas sin consumer en Neon, mas el indice parcial
asociado a `referrer`:

- `tracking_events`: cloudfront_meta, expires_at, page_url, page_title,
  referrer
- `contacts`: cloudfront_meta
- Indice: idx_tracking_referrer (parcial sobre referrer IS NOT NULL)

`page_path` y su indice `idx_tracking_page_path` NO se tocan: siguen
siendo la columna canonica para analitica de "trafico por seccion".

Orden duro en `upgrade()`: indice ANTES que la columna (referrer).
`downgrade()` invierte el orden y recrea `page_url` como NULLABLE (no
NOT NULL) para que el revert no falle si hay rows nuevas con page_url
NULL post-upgrade.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Drop columnas huerfanas + idx_tracking_referrer."""
    # tracking_events ---------------------------------------------------
    # 1. drop indice parcial antes de dropear la columna referrer.
    op.drop_index(
        'idx_tracking_referrer',
        table_name='tracking_events',
        postgresql_where=sa.text('referrer IS NOT NULL'),
    )
    # 2. drop columnas. En PG14+ drop_column propaga a particiones.
    op.drop_column('tracking_events', 'referrer')
    op.drop_column('tracking_events', 'page_title')
    op.drop_column('tracking_events', 'page_url')
    op.drop_column('tracking_events', 'expires_at')
    op.drop_column('tracking_events', 'cloudfront_meta')

    # contacts ----------------------------------------------------------
    op.drop_column('contacts', 'cloudfront_meta')


def downgrade() -> None:
    """Recrea columnas + indice. page_url vuelve NULLABLE."""
    # contacts ----------------------------------------------------------
    op.add_column(
        'contacts',
        sa.Column('cloudfront_meta', JSONB(), nullable=True),
    )

    # tracking_events ---------------------------------------------------
    op.add_column(
        'tracking_events',
        sa.Column('cloudfront_meta', JSONB(), nullable=True),
    )
    op.add_column(
        'tracking_events',
        sa.Column(
            'expires_at',
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    # page_url vuelve NULLABLE (originalmente NOT NULL): si hay rows
    # post-upgrade no podriamos recrearla como NOT NULL sin un DEFAULT.
    op.add_column(
        'tracking_events',
        sa.Column('page_url', sa.Text(), nullable=True),
    )
    op.add_column(
        'tracking_events',
        sa.Column('page_title', sa.Text(), nullable=True),
    )
    op.add_column(
        'tracking_events',
        sa.Column('referrer', sa.Text(), nullable=True),
    )
    op.create_index(
        'idx_tracking_referrer',
        'tracking_events',
        ['referrer'],
        unique=False,
        postgresql_where=sa.text('referrer IS NOT NULL'),
    )
