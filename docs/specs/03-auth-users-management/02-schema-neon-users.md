# 02. Schema Neon — extension `auth_users` + tablas de gestion

## Delta del schema

```text
auth_users  (extension)
─────────────────────
 + display_name varchar(64)
 + locale varchar(8)  default 'en'  CHECK locale IN ('en', 'es')
 + timezone varchar(64)  default 'UTC'
 + marketing_consent boolean default false
 + privacy_policy_version varchar(16) NULL
 + deleted_at timestamptz NULL
 (existentes del plan 01)

auth_user_sessions
──────────────────
 id           uuid PK uuidv7()
 user_id      uuid FK auth_users.id ON DELETE CASCADE
 family_id    uuid UNIQUE  -- 1 row por refresh family
 device_info  jsonb        -- {browser, os, device_type}
 ip           inet
 country      char(2) NULL
 user_agent   text
 created_at   timestamptz
 last_active_at timestamptz

auth_user_admin_actions
────────────────────────
 id              uuid PK
 admin_user_id   uuid FK auth_users.id ON DELETE SET NULL
 target_user_id  uuid FK auth_users.id ON DELETE SET NULL
 action          varchar(64)   -- 'disable'|'enable'|'force-logout'|'delete'|...
 metadata        jsonb NULL    -- {reason, ip_target, etc.}
 ip              inet
 user_agent      text NULL
 created_at      timestamptz

auth_user_consent_log
─────────────────────
 id          uuid PK
 user_id     uuid FK auth_users.id ON DELETE CASCADE
 field       varchar(32)        -- 'marketing_consent'|'privacy_policy'
 old_value   text
 new_value   text
 ip          inet
 user_agent  text NULL
 created_at  timestamptz
```

## Migration 00000004

```python
"""auth_users_extension

Revision ID: 00000004
Revises: 00000003
Create Date: 2026-05-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '00000004'
down_revision = '00000003'


def upgrade() -> None:
    # 1. Extender auth_users con columnas nuevas
    op.add_column('auth_users',
        sa.Column('display_name', sa.String(64), nullable=True))
    op.add_column('auth_users',
        sa.Column('locale', sa.String(8), nullable=False, server_default='en'))
    op.add_column('auth_users',
        sa.Column('timezone', sa.String(64), nullable=False, server_default='UTC'))
    op.add_column('auth_users',
        sa.Column('marketing_consent', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('auth_users',
        sa.Column('privacy_policy_version', sa.String(16), nullable=True))
    op.add_column('auth_users',
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))

    # 2. CHECK locale + partial unique index para soporte de soft-delete
    op.create_check_constraint(
        'ck_auth_users_locale', 'auth_users',
        "locale IN ('en', 'es')",
    )
    # Drop el UNIQUE viejo de email (era full)
    op.drop_constraint('auth_users_email_key', 'auth_users', type_='unique')
    # Reemplazar con partial unique index
    op.create_index(
        'ux_auth_users_email_active', 'auth_users', ['email'],
        unique=True, postgresql_where=sa.text('deleted_at IS NULL'),
    )
    op.create_index(
        'ix_auth_users_deleted_at', 'auth_users', ['deleted_at'],
    )

    # 3. ALTER TYPE auth_link_kind ADD VALUE 'email-change'
    op.execute("ALTER TYPE auth_link_kind ADD VALUE IF NOT EXISTS 'email-change'")

    # 4. auth_user_sessions
    op.create_table(
        'auth_user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuidv7()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('family_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('device_info', postgresql.JSONB(), nullable=True),
        sa.Column('ip', postgresql.INET(), nullable=True),
        sa.Column('country', sa.CHAR(2), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['auth_users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_auth_user_sessions_user_active',
                    'auth_user_sessions', ['user_id', 'last_active_at'])

    # 5. auth_user_admin_actions
    op.create_table(
        'auth_user_admin_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuidv7()')),
        sa.Column('admin_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('target_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('ip', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['admin_user_id'], ['auth_users.id'],
                                ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['target_user_id'], ['auth_users.id'],
                                ondelete='SET NULL'),
    )
    op.create_index('ix_auth_admin_actions_target_ts',
                    'auth_user_admin_actions',
                    ['target_user_id', 'created_at'])

    # 6. auth_user_consent_log
    op.create_table(
        'auth_user_consent_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuidv7()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('field', sa.String(32), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('ip', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['auth_users.id'],
                                ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('auth_user_consent_log')
    op.drop_table('auth_user_admin_actions')
    op.drop_table('auth_user_sessions')

    # NO se puede DROP VALUE de un enum en PG. Para downgrade limpio
    # habria que recrear el tipo (destructivo). En este plan asumimos
    # downgrade en branch Neon de prueba; en prod NO se hace downgrade.
    # Aqui dejamos el value en el enum (forward-only en prod).
    pass

    op.drop_index('ix_auth_users_deleted_at', 'auth_users')
    op.drop_index('ux_auth_users_email_active', 'auth_users')
    op.create_unique_constraint('auth_users_email_key', 'auth_users', ['email'])

    op.drop_constraint('ck_auth_users_locale', 'auth_users', type_='check')

    op.drop_column('auth_users', 'deleted_at')
    op.drop_column('auth_users', 'privacy_policy_version')
    op.drop_column('auth_users', 'marketing_consent')
    op.drop_column('auth_users', 'timezone')
    op.drop_column('auth_users', 'locale')
    op.drop_column('auth_users', 'display_name')
```

> **Importante**: `ALTER TYPE ADD VALUE` no se puede revertir en
> PostgreSQL sin recrear el tipo. El `downgrade()` deja `email-change`
> en el enum. En prod NO se corre downgrade; en branches de prueba es
> aceptable.

## Modelos SQLAlchemy (delta)

```text
serverless/lambda/shared/db/models/auth/
├── user.py             # MODIFICAR — agregar columnas nuevas
├── enums.py            # MODIFICAR — agregar 'email-change' a AuthLinkKind
├── user_session.py     # NUEVO — AuthUserSession
├── admin_action.py     # NUEVO — AuthUserAdminAction
└── consent_log.py      # NUEVO — AuthUserConsentLog
```

`user.py` (delta):

```python
class AuthUser(UUIDPKMixin, TimestampMixin, Base):
    # ... existentes del plan 01

    # NUEVOS del plan 03
    display_name: Mapped[str | None] = mapped_column(String(64))
    locale: Mapped[str] = mapped_column(String(8), default='en', nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default='UTC', nullable=False)
    marketing_consent: Mapped[bool] = mapped_column(default=False, nullable=False)
    privacy_policy_version: Mapped[str | None] = mapped_column(String(16))
    deleted_at: Mapped[datetime | None]

    __table_args__ = (
        # ... existentes
        CheckConstraint("locale IN ('en', 'es')", name='ck_auth_users_locale'),
        Index('ux_auth_users_email_active', 'email', unique=True,
              postgresql_where=sa.text('deleted_at IS NULL')),
        Index('ix_auth_users_deleted_at', 'deleted_at'),
    )
```

`user_session.py`:

```python
class AuthUserSession(UUIDPKMixin, Base):
    __tablename__ = 'auth_user_sessions'

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey('auth_users.id', ondelete='CASCADE'), nullable=False)
    family_id: Mapped[UUID] = mapped_column(unique=True, nullable=False)
    device_info: Mapped[dict | None] = mapped_column(JSONB)
    ip: Mapped[str | None] = mapped_column(INET)
    country: Mapped[str | None] = mapped_column(CHAR(2))
    user_agent: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(
        server_default=sa.text('now()'), nullable=False)
    last_active_at: Mapped[datetime] = mapped_column(
        server_default=sa.text('now()'), nullable=False)
```

## Repository extensions

`shared/db/repositories/auth_users.py` (NUEVO archivo, separa lo del
plan 01 que estaba en `auth.py`):

```python
def get_user_by_id(session, *, user_id) -> AuthUser | None: ...
def update_profile(session, *, user_id, **fields) -> AuthUser: ...
def soft_delete_user(session, *, user_id, anonymized_email) -> None: ...
def hard_delete_user(session, *, user_id) -> None: ...
def list_users_paginated(session, *, cursor, page_size, status_filter) -> list[AuthUser]: ...
def disable_user(session, *, user_id) -> None: ...
def enable_user(session, *, user_id) -> None: ...

def insert_user_session(session, *, user_id, family_id, device_info, ip, country, user_agent) -> AuthUserSession: ...
def update_session_activity(session, *, family_id) -> bool: ...
def rotate_session_family_id(session, *, old_family_id, new_family_id) -> bool: ...
def list_user_sessions(session, *, user_id) -> list[AuthUserSession]: ...
def revoke_session(session, *, user_id, session_id) -> bool: ...
def revoke_all_user_sessions(session, *, user_id) -> list[UUID]: ...  # retorna family_ids para blacklist

def insert_admin_action(session, *, admin_user_id, target_user_id, action, metadata, ip) -> None: ...
def list_admin_actions(session, *, from_date, to_date, page_size) -> list[AuthUserAdminAction]: ...

def insert_consent_log(session, *, user_id, field, old_value, new_value, ip, user_agent) -> None: ...
```

## Indices justificacion

| Indice | Justificacion |
|--------|---------------|
| `ux_auth_users_email_active` (partial unique) | Permite re-uso de email tras soft-delete (AC-27) |
| `ix_auth_users_deleted_at` | Filtro `WHERE deleted_at IS NULL` en queries de list |
| `ix_auth_user_sessions_user_active` | List sessions del user |
| `auth_user_sessions.family_id` UNIQUE | Lookup por family_id en rotation/revoke |
| `ix_auth_admin_actions_target_ts` | Audit historico de un target user |

## Update al ER permanente

Al cerrar plan 03: actualizar `docs/diagrams/db-er.mmd` con:
- columnas nuevas de `auth_users`
- 3 tablas nuevas + relaciones FK
