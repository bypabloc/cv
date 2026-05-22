"""add profile_niches

Revision ID: 79bacfd3c091
Revises: 81c2cc51db34
Create Date: 2026-05-22 11:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '79bacfd3c091'
down_revision: str | None = '81c2cc51db34'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Union profile <-> niche. El profile es singleton, pero sus niches se
    # persisten igual para que la DB sea fuente de verdad completa del CV.
    # Mismo patron que las demas tablas `<entidad>_niches`.
    op.create_table(
        'profile_niches',
        sa.Column('profile_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('niche_id', sa.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(
            ['profile_id'],
            ['profile.id'],
            name=op.f('fk_profile_niches_profile_id_profile'),
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['niche_id'],
            ['niches.id'],
            name=op.f('fk_profile_niches_niche_id_niches'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint(
            'profile_id', 'niche_id', name=op.f('pk_profile_niches')
        ),
    )


def downgrade() -> None:
    op.drop_table('profile_niches')
