"""auth_users_extension

Revision ID: 00000004
Revises: 00000003
Create Date: 2026-05-28

Extension de gestion de usuarios del dominio auth (plan
03-auth-users-management). Agrega:

- columnas a `auth_users`: `display_name`, `locale`, `timezone`,
  `marketing_consent`, `privacy_policy_version`, `deleted_at`.
- CHECK `ck_auth_users_locale` (locale IN ('en', 'es')).
- reemplaza el UNIQUE full de `auth_users.email` por un partial unique
  index `ux_auth_users_email_active` (WHERE deleted_at IS NULL) — permite
  re-usar un email tras el soft-delete del user.
- index `ix_auth_users_deleted_at`.
- valor `email-change` al enum `auth_link_kind` (reuso de
  `auth_magic_links` para el flujo de cambio de email).
- columna `auth_magic_links.metadata` (jsonb) — lleva `{new_email}` del
  flujo email-change.
- tabla `auth_user_sessions`        (sesiones activas por family_id).
- tabla `auth_user_admin_actions`   (audit inmutable de acciones admin).
- tabla `auth_user_consent_log`     (log GDPR de cambios de consent).

Decisiones:
- `ALTER TYPE auth_link_kind ADD VALUE` NO puede correr dentro de una
  transaccion en PostgreSQL; se ejecuta en `autocommit_block()`. Es la
  PRIMERA migration del repo en usar este patron.
- PostgreSQL NO soporta `ALTER TYPE ... DROP VALUE`: el downgrade NO
  remueve `email-change` del enum (forward-only en prod, mismo criterio
  que la 00000003). La idempotencia up/down/up de AC-25 NO exige que el
  catalogo del enum vuelva al set original, solo que columnas/tablas se
  recreen.
- soft-delete del user es un UPDATE (`deleted_at` + email anonimo): las FK
  ON DELETE CASCADE NO se disparan (reaccionan a DELETE, no a UPDATE); el
  borrado de credentials/mfa/etc. lo hace el service con DELETE explicitos.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '00000004'
down_revision: str | None = '00000003'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- 1. Columnas nuevas de auth_users ---
    op.add_column(
        'auth_users',
        sa.Column('display_name', sa.String(length=64), nullable=True),
    )
    op.add_column(
        'auth_users',
        sa.Column(
            'locale', sa.String(length=8),
            server_default=sa.text("'en'"), nullable=False,
        ),
    )
    op.add_column(
        'auth_users',
        sa.Column(
            'timezone', sa.String(length=64),
            server_default=sa.text("'UTC'"), nullable=False,
        ),
    )
    op.add_column(
        'auth_users',
        sa.Column(
            'marketing_consent', sa.Boolean(),
            server_default=sa.text('false'), nullable=False,
        ),
    )
    op.add_column(
        'auth_users',
        sa.Column(
            'privacy_policy_version', sa.String(length=16), nullable=True,
        ),
    )
    op.add_column(
        'auth_users',
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )

    # --- 2. CHECK locale ---
    op.create_check_constraint(
        'ck_auth_users_locale', 'auth_users', "locale IN ('en', 'es')",
    )

    # --- 3. Partial unique index de email (reemplaza el UNIQUE full) ---
    # El UNIQUE full lo creo la 00000002 con la naming convention
    # (`uq_auth_users_email`). Lo dropeamos y lo reemplazamos por un
    # partial unique index que solo aplica a los users no borrados.
    op.drop_constraint('uq_auth_users_email', 'auth_users', type_='unique')
    op.create_index(
        'ux_auth_users_email_active',
        'auth_users',
        ['email'],
        unique=True,
        postgresql_where=sa.text('deleted_at IS NULL'),
    )
    op.create_index(
        'ix_auth_users_deleted_at', 'auth_users', ['deleted_at'],
    )

    # --- 4. Valor 'email-change' al enum auth_link_kind ---
    # ALTER TYPE ... ADD VALUE NO corre dentro de una transaccion (Alembic
    # envuelve upgrade() en una). El autocommit_block local lo permite.
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE auth_link_kind ADD VALUE IF NOT EXISTS 'email-change'",
        )

    # --- 5. auth_magic_links.metadata (jsonb) ---
    op.add_column(
        'auth_magic_links',
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
    )

    # --- 6. auth_user_sessions ---
    op.create_table(
        'auth_user_sessions',
        sa.Column(
            'id', sa.UUID(as_uuid=False),
            server_default=sa.text('uuidv7()'), nullable=False,
        ),
        sa.Column('user_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('family_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('device_info', postgresql.JSONB(), nullable=True),
        sa.Column('ip', postgresql.INET(), nullable=True),
        sa.Column('country', sa.CHAR(length=2), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.Column(
            'last_active_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['auth_users.id'],
            name=op.f('fk_auth_user_sessions_user_id_auth_users'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_auth_user_sessions')),
        sa.UniqueConstraint(
            'family_id', name='uq_auth_user_sessions_family_id',
        ),
    )
    op.create_index(
        'ix_auth_user_sessions_user_active', 'auth_user_sessions',
        ['user_id', 'last_active_at'],
    )

    # --- 7. auth_user_admin_actions ---
    op.create_table(
        'auth_user_admin_actions',
        sa.Column(
            'id', sa.UUID(as_uuid=False),
            server_default=sa.text('uuidv7()'), nullable=False,
        ),
        sa.Column('admin_user_id', sa.UUID(as_uuid=False), nullable=True),
        sa.Column('target_user_id', sa.UUID(as_uuid=False), nullable=True),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('ip', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['admin_user_id'], ['auth_users.id'],
            name=op.f('fk_auth_user_admin_actions_admin_user_id_auth_users'),
            ondelete='SET NULL',
        ),
        sa.ForeignKeyConstraint(
            ['target_user_id'], ['auth_users.id'],
            name=op.f('fk_auth_user_admin_actions_target_user_id_auth_users'),
            ondelete='SET NULL',
        ),
        sa.PrimaryKeyConstraint(
            'id', name=op.f('pk_auth_user_admin_actions'),
        ),
    )
    op.create_index(
        'ix_auth_admin_actions_target_ts', 'auth_user_admin_actions',
        ['target_user_id', 'created_at'],
    )

    # --- 8. auth_user_consent_log ---
    op.create_table(
        'auth_user_consent_log',
        sa.Column(
            'id', sa.UUID(as_uuid=False),
            server_default=sa.text('uuidv7()'), nullable=False,
        ),
        sa.Column('user_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('field', sa.String(length=32), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('ip', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['auth_users.id'],
            name=op.f('fk_auth_user_consent_log_user_id_auth_users'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_auth_user_consent_log')),
    )


def downgrade() -> None:
    op.drop_table('auth_user_consent_log')
    op.drop_index(
        'ix_auth_admin_actions_target_ts',
        table_name='auth_user_admin_actions',
    )
    op.drop_table('auth_user_admin_actions')
    op.drop_index(
        'ix_auth_user_sessions_user_active',
        table_name='auth_user_sessions',
    )
    op.drop_table('auth_user_sessions')

    op.drop_column('auth_magic_links', 'metadata')

    # PostgreSQL NO soporta ALTER TYPE ... DROP VALUE. El valor
    # 'email-change' queda en el enum auth_link_kind (forward-only). En
    # prod NO se corre downgrade. En un branch de prueba el segundo
    # `upgrade head` re-ejecuta ADD VALUE IF NOT EXISTS (no-op).

    op.drop_index('ix_auth_users_deleted_at', table_name='auth_users')
    op.drop_index('ux_auth_users_email_active', table_name='auth_users')
    op.create_unique_constraint(
        'uq_auth_users_email', 'auth_users', ['email'],
    )
    op.drop_constraint(
        'ck_auth_users_locale', 'auth_users', type_='check',
    )

    op.drop_column('auth_users', 'deleted_at')
    op.drop_column('auth_users', 'privacy_policy_version')
    op.drop_column('auth_users', 'marketing_consent')
    op.drop_column('auth_users', 'timezone')
    op.drop_column('auth_users', 'locale')
    op.drop_column('auth_users', 'display_name')
