"""password_required_flag

Revision ID: 00000006
Revises: 00000005
Create Date: 2026-06-04

Agrega el flag `required` (factor exigido al loguear) a la tabla de la
contrasena (`auth_credentials`), para el plan login-mfa-list-redesign: la
contrasena pasa de ser un GATE previo a ser UN metodo mas de la lista de
factores que el login puede exigir, junto a totp / email_code / webauthn /
passwordless.

- columna `auth_credentials.required` (boolean, NOT NULL, default true).

Decisiones:
- `server_default=true` (a diferencia de la 00000005 que usa false): la
  contrasena, si EXISTE, se exige por defecto. Asi todo user existente con
  credentials preserva exactamente el comportamiento actual (la password
  siempre se exigia cuando existia). Con `false` un user con password quedaria
  sin ningun factor exigido en el modelo de lista -> regresion de seguridad
  critica (cualquiera con el email entraria sin la password). `true` es el
  default seguro.
- La password participa del guard anti-lockout "siempre >=1 required": no se
  puede desmarcar (`security.password.set-required` required=false) si es el
  unico factor requerido del user.
- El `downgrade()` elimina la columna (reversible completo).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '00000006'
down_revision: str | None = '00000005'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'auth_credentials',
        sa.Column(
            'required', sa.Boolean(),
            server_default=sa.text('true'), nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column('auth_credentials', 'required')
