"""mfa_required_flag

Revision ID: 00000005
Revises: 00000004
Create Date: 2026-06-03

Agrega el flag `required` (metodo requerido al loguear) a los dos modelos de
metodos MFA del dominio auth (plan admin-security-overview, bloque B):

- columna `auth_mfa_methods.required`        (boolean, NOT NULL, default false).
- columna `auth_webauthn_credentials.required` (boolean, NOT NULL, default
  false).

Un metodo con `required=true` se EXIGE en el login (multi-factor: si el user
marca varios, el login pide todos). El fallback anti-lockout (recovery code +
email-code de emergencia) saltea los requeridos. `required` es independiente de
`preferred` (que solo sugiere el metodo por defecto) y de `disabled_at` (un
metodo desactivado no se exige aunque tenga `required=true`; el login consulta
solo los activos + requeridos).

Decisiones:
- `server_default=false` permite agregar la columna NOT NULL sin reescribir las
  filas existentes (todas nacen no-requeridas, preservando el comportamiento
  actual: el login propone, con uno basta).
- El `downgrade()` elimina ambas columnas (reversible completo, sin enums ni
  constraints que PostgreSQL no sepa revertir).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '00000005'
down_revision: str | None = '00000004'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'auth_mfa_methods',
        sa.Column(
            'required', sa.Boolean(),
            server_default=sa.text('false'), nullable=False,
        ),
    )
    op.add_column(
        'auth_webauthn_credentials',
        sa.Column(
            'required', sa.Boolean(),
            server_default=sa.text('false'), nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column('auth_webauthn_credentials', 'required')
    op.drop_column('auth_mfa_methods', 'required')
