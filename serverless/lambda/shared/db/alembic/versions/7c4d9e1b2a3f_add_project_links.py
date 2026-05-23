"""add project links jsonb

Revision ID: 7c4d9e1b2a3f
Revises: 649aa862c0fa
Create Date: 2026-05-23 13:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '7c4d9e1b2a3f'
down_revision: str | None = '649aa862c0fa'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Agrega columna `links` JSONB nullable a projects.

    Modela uno o varios sitios alternos en produccion del mismo proyecto
    (caso: destacame-debt-chile cubre 3 marcas comerciales). Estructura:
    `[{"label": {"es": "X", "en": "X"}, "url": "https://..."}, ...]`.
    Nullable porque la mayoria de proyectos tienen 1 sola URL en `url`.
    """
    op.add_column(
        'projects',
        sa.Column('links', JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('projects', 'links')
