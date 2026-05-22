"""add cv country and metrics_estimated

Revision ID: 649aa862c0fa
Revises: 79bacfd3c091
Create Date: 2026-05-22 13:25:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '649aa862c0fa'
down_revision: str | None = '79bacfd3c091'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # experiences.country: NOT NULL. server_default='' temporal para que el
    # ADD COLUMN no falle si la tabla ya tiene filas; se retira despues.
    op.add_column(
        'experiences',
        sa.Column(
            'country',
            sa.String(length=120),
            nullable=False,
            server_default='',
        ),
    )
    op.alter_column('experiences', 'country', server_default=None)
    # metrics_estimated en experiences y projects. server_default=false es un
    # default real (no temporal): coincide con el default del modelo.
    op.add_column(
        'experiences',
        sa.Column(
            'metrics_estimated',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        'projects',
        sa.Column(
            'metrics_estimated',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column('projects', 'metrics_estimated')
    op.drop_column('experiences', 'metrics_estimated')
    op.drop_column('experiences', 'country')
