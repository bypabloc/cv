"""auth_schema

Revision ID: 00000002
Revises: 00000001
Create Date: 2026-05-28

Schema del dominio de autenticacion: 5 tablas + 3 enums PG.

- auth_users         (pk uuid, email citext UK, status enum, ...)
- auth_credentials   (pk user_id, password_hash, algo)
- auth_email_codes   (pk uuid, user_id FK, code_hash bytea, kind enum, ...)
- auth_magic_links   (pk uuid, user_id FK, token_hash bytea UK, kind enum, ...)
- auth_audit_log     (pk uuid, user_id FK NULL, event, success, metadata jsonb, ...)

Decisiones:
- `email` es CITEXT (no STRING) para lookup case-insensitive sin LOWER().
  El service guarda lowercased igual; CITEXT garantiza que un user
  registrado como `Foo@x.com` no se duplique como `foo@x.com`.
- `auth_users.profile_id` FK NULLABLE a `cv_profiles.id` con ON DELETE
  SET NULL — solo el row de Pablo apuntara (manual).
- `auth_email_codes.code_hash` y `auth_magic_links.token_hash` son
  SHA-256 (32 bytes BYTEA). El code/token en plain text NUNCA se guarda.
- `auth_magic_links.token_hash` UNIQUE para que la query
  `WHERE token_hash = ?` use el index.
- 3 ENUMs PG creados con `op.execute('CREATE TYPE ...')` para asegurar
  el orden exacto de valores (necesario para downgrade reproducible).
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '00000002'
down_revision: str | None = '00000001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- ENUMs ---
    op.execute(
        "CREATE TYPE auth_user_status AS ENUM ("
        "'pending', 'active', 'disabled', 'locked', 'deleted')",
    )
    op.execute(
        "CREATE TYPE auth_code_kind AS ENUM ("
        "'register', 'login', 'password_reset')",
    )
    op.execute(
        "CREATE TYPE auth_link_kind AS ENUM ("
        "'register', 'login', 'password_reset')",
    )

    auth_user_status_enum = postgresql.ENUM(
        'pending', 'active', 'disabled', 'locked', 'deleted',
        name='auth_user_status', create_type=False,
    )
    auth_code_kind_enum = postgresql.ENUM(
        'register', 'login', 'password_reset',
        name='auth_code_kind', create_type=False,
    )
    auth_link_kind_enum = postgresql.ENUM(
        'register', 'login', 'password_reset',
        name='auth_link_kind', create_type=False,
    )

    # --- auth_users ---
    op.create_table(
        'auth_users',
        sa.Column(
            'id', sa.UUID(as_uuid=False),
            server_default=sa.text('uuidv7()'), nullable=False,
        ),
        sa.Column('email', postgresql.CITEXT(), nullable=False),
        sa.Column(
            'status', auth_user_status_enum,
            server_default=sa.text("'pending'::auth_user_status"),
            nullable=False,
        ),
        sa.Column('profile_id', sa.UUID(as_uuid=False), nullable=True),
        sa.Column(
            'email_verified_at', sa.DateTime(timezone=True), nullable=True,
        ),
        sa.Column(
            'password_set_at', sa.DateTime(timezone=True), nullable=True,
        ),
        sa.Column(
            'locked_until', sa.DateTime(timezone=True), nullable=True,
        ),
        sa.Column(
            'last_login_at', sa.DateTime(timezone=True), nullable=True,
        ),
        sa.Column(
            'failed_attempts', sa.Integer(),
            server_default=sa.text('0'), nullable=False,
        ),
        sa.Column(
            'created_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['profile_id'], ['cv_profiles.id'],
            name=op.f('fk_auth_users_profile_id_cv_profiles'),
            ondelete='SET NULL',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_auth_users')),
        sa.UniqueConstraint('email', name=op.f('uq_auth_users_email')),
    )

    # --- auth_credentials ---
    op.create_table(
        'auth_credentials',
        sa.Column('user_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column(
            'algo', sa.String(length=32),
            server_default=sa.text("'argon2id'"), nullable=False,
        ),
        sa.Column(
            'password_set_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.Column(
            'last_change_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['auth_users.id'],
            name=op.f('fk_auth_credentials_user_id_auth_users'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint(
            'user_id', name=op.f('pk_auth_credentials'),
        ),
    )

    # --- auth_email_codes ---
    op.create_table(
        'auth_email_codes',
        sa.Column(
            'id', sa.UUID(as_uuid=False),
            server_default=sa.text('uuidv7()'), nullable=False,
        ),
        sa.Column('user_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('code_hash', postgresql.BYTEA(), nullable=False),
        sa.Column('kind', auth_code_kind_enum, nullable=False),
        sa.Column(
            'attempts', sa.Integer(),
            server_default=sa.text('0'), nullable=False,
        ),
        sa.Column(
            'expires_at', sa.DateTime(timezone=True), nullable=False,
        ),
        sa.Column(
            'consumed_at', sa.DateTime(timezone=True), nullable=True,
        ),
        sa.Column(
            'created_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['auth_users.id'],
            name=op.f('fk_auth_email_codes_user_id_auth_users'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_auth_email_codes')),
    )
    op.create_index(
        'ix_auth_email_codes_user_kind',
        'auth_email_codes',
        ['user_id', 'kind', 'consumed_at'],
    )

    # --- auth_magic_links ---
    op.create_table(
        'auth_magic_links',
        sa.Column(
            'id', sa.UUID(as_uuid=False),
            server_default=sa.text('uuidv7()'), nullable=False,
        ),
        sa.Column('user_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('token_hash', postgresql.BYTEA(), nullable=False),
        sa.Column('kind', auth_link_kind_enum, nullable=False),
        sa.Column(
            'expires_at', sa.DateTime(timezone=True), nullable=False,
        ),
        sa.Column(
            'consumed_at', sa.DateTime(timezone=True), nullable=True,
        ),
        sa.Column(
            'created_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.Column('ip', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ['user_id'], ['auth_users.id'],
            name=op.f('fk_auth_magic_links_user_id_auth_users'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_auth_magic_links')),
        sa.UniqueConstraint(
            'token_hash', name=op.f('uq_auth_magic_links_token_hash'),
        ),
    )

    # --- auth_audit_log ---
    op.create_table(
        'auth_audit_log',
        sa.Column(
            'id', sa.UUID(as_uuid=False),
            server_default=sa.text('uuidv7()'), nullable=False,
        ),
        sa.Column('user_id', sa.UUID(as_uuid=False), nullable=True),
        sa.Column('event', sa.String(length=64), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_code', sa.String(length=64), nullable=True),
        sa.Column('ip', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('niche', sa.String(length=32), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['auth_users.id'],
            name=op.f('fk_auth_audit_log_user_id_auth_users'),
            ondelete='SET NULL',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_auth_audit_log')),
    )
    op.create_index(
        'ix_auth_audit_log_user_event_ts',
        'auth_audit_log',
        ['user_id', 'event', 'created_at'],
    )


def downgrade() -> None:
    op.drop_index(
        'ix_auth_audit_log_user_event_ts', table_name='auth_audit_log',
    )
    op.drop_table('auth_audit_log')

    op.drop_table('auth_magic_links')

    op.drop_index(
        'ix_auth_email_codes_user_kind', table_name='auth_email_codes',
    )
    op.drop_table('auth_email_codes')

    op.drop_table('auth_credentials')
    op.drop_table('auth_users')

    op.execute('DROP TYPE IF EXISTS auth_link_kind')
    op.execute('DROP TYPE IF EXISTS auth_code_kind')
    op.execute('DROP TYPE IF EXISTS auth_user_status')
