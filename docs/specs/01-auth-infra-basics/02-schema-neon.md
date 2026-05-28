# 02. Schema Neon — dominio `auth_*`

## ER ASCII (solo tablas nuevas + relacion a cv_profiles)

```text
cv_profiles                       auth_users
─────────────                     ──────────────────
 id  uuid PK                      id              uuid PK
 email varchar                    email           citext UK (lowercased)
 name  varchar                    status          auth_user_status
                                  profile_id     uuid FK NULL --> cv_profiles.id
                                  email_verified_at  timestamptz NULL
                                  password_set_at    timestamptz NULL
                                  locked_until       timestamptz NULL
                                  last_login_at      timestamptz NULL
                                  failed_attempts    int default 0
                                  created_at         timestamptz
                                  updated_at         timestamptz
                                       |
                                       | 1
                ┌──────────────────────┼──────────────────────────┐
                | 0..1                 | 0..*                     | 0..*
                v                      v                          v
       auth_credentials       auth_email_codes           auth_magic_links
       ──────────────────     ────────────────────       ────────────────────
        user_id  uuid PK,FK    id              uuid PK    id           uuid PK
        password_hash  text    user_id         uuid FK    user_id      uuid FK
        algo varchar           code_hash       bytea      token_hash   bytea
        password_set_at  ts    kind            code_kind  kind         link_kind
        last_change_at ts      attempts        int        consumed_at  ts NULL
                               expires_at      timestamptz expires_at  timestamptz
                               consumed_at     timestamptz created_at  ts
                               created_at      timestamptz ip          inet NULL
                                                          user_agent   text NULL

                                       auth_audit_log
                                       ──────────────────
                                        id              uuid PK
                                        user_id         uuid FK NULL
                                        event           varchar (e.g. 'register.start')
                                        success         boolean
                                        error_code      varchar NULL
                                        ip              inet NULL
                                        user_agent      text NULL
                                        niche           varchar NULL
                                        metadata        jsonb NULL
                                        created_at      timestamptz
```

## DDL conceptual (la migration la genera Alembic autogenerate; el dev revisa)

```python
# serverless/lambda/shared/db/alembic/versions/00000002_auth_schema.py
"""auth_schema

Revision ID: 00000002
Revises: 00000001
Create Date: 2026-05-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '00000002'
down_revision = '00000001'

def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS citext')

    # 1. Enums
    auth_user_status = postgresql.ENUM(
        'pending', 'active', 'disabled', 'locked', 'deleted',
        name='auth_user_status',
    )
    auth_user_status.create(op.get_bind())

    code_kind = postgresql.ENUM(
        'register', 'login', 'password_reset',
        name='auth_code_kind',
    )
    code_kind.create(op.get_bind())

    link_kind = postgresql.ENUM(
        'register', 'login', 'password_reset',
        name='auth_link_kind',
    )
    link_kind.create(op.get_bind())

    # 2. auth_users
    op.create_table(
        'auth_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuidv7()')),
        sa.Column('email', postgresql.CITEXT(), nullable=False, unique=True),
        sa.Column('status', auth_user_status, nullable=False,
                  server_default='pending'),
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_set_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_attempts', sa.Integer(), nullable=False,
                  server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['profile_id'], ['cv_profiles.id'],
                                ondelete='SET NULL'),
    )
    op.create_index('ix_auth_users_status', 'auth_users', ['status'])
    op.create_index('ix_auth_users_profile_id', 'auth_users', ['profile_id'])

    # 3. auth_credentials (1-to-0..1 con auth_users)
    op.create_table(
        'auth_credentials',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('algo', sa.String(32), nullable=False, server_default='argon2id'),
        sa.Column('password_set_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('last_change_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['auth_users.id'],
                                ondelete='CASCADE'),
    )

    # 4. auth_email_codes
    op.create_table(
        'auth_email_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuidv7()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code_hash', postgresql.BYTEA(), nullable=False),
        sa.Column('kind', code_kind, nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['auth_users.id'],
                                ondelete='CASCADE'),
    )
    op.create_index('ix_auth_email_codes_user_kind',
                    'auth_email_codes', ['user_id', 'kind', 'consumed_at'])

    # 5. auth_magic_links
    op.create_table(
        'auth_magic_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuidv7()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', postgresql.BYTEA(), nullable=False, unique=True),
        sa.Column('kind', link_kind, nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('ip', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['auth_users.id'],
                                ondelete='CASCADE'),
    )

    # 6. auth_audit_log (insert-only, retencion via partitioning futuro)
    op.create_table(
        'auth_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuidv7()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event', sa.String(64), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_code', sa.String(64), nullable=True),
        sa.Column('ip', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('niche', sa.String(32), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
    )
    op.create_index('ix_auth_audit_log_user_event_ts',
                    'auth_audit_log', ['user_id', 'event', 'created_at'])

def downgrade() -> None:
    op.drop_table('auth_audit_log')
    op.drop_table('auth_magic_links')
    op.drop_table('auth_email_codes')
    op.drop_table('auth_credentials')
    op.drop_table('auth_users')
    op.execute('DROP TYPE IF EXISTS auth_link_kind')
    op.execute('DROP TYPE IF EXISTS auth_code_kind')
    op.execute('DROP TYPE IF EXISTS auth_user_status')
```

## SQLAlchemy models (esqueleto, ubicacion `shared/db/models/auth/`)

```text
serverless/lambda/shared/db/models/auth/
├── __init__.py        # re-exporta los 5 modelos + los 3 enums
├── enums.py           # AuthUserStatus, AuthCodeKind, AuthLinkKind (Python enums)
├── user.py            # AuthUser
├── credentials.py     # AuthCredentials
├── email_code.py      # AuthEmailCode
├── magic_link.py      # AuthMagicLink
└── audit_log.py       # AuthAuditLog
```

Patron de cada modelo:

```python
# serverless/lambda/shared/db/models/auth/user.py
from datetime import datetime
from uuid import UUID
from sqlalchemy import CheckConstraint, ForeignKey, Index
from sqlalchemy.dialects.postgresql import CITEXT, ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.db.base import Base, UUIDPKMixin, TimestampMixin
from .enums import AuthUserStatus


class AuthUser(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = 'auth_users'

    email: Mapped[str] = mapped_column(CITEXT(), unique=True, nullable=False)
    status: Mapped[AuthUserStatus] = mapped_column(
        PgEnum(AuthUserStatus, name='auth_user_status'),
        nullable=False, default=AuthUserStatus.PENDING,
    )
    profile_id: Mapped[UUID | None] = mapped_column(
        ForeignKey('cv_profiles.id', ondelete='SET NULL'), nullable=True,
    )
    email_verified_at: Mapped[datetime | None]
    password_set_at: Mapped[datetime | None]
    locked_until: Mapped[datetime | None]
    last_login_at: Mapped[datetime | None]
    failed_attempts: Mapped[int] = mapped_column(default=0, nullable=False)

    credentials: Mapped['AuthCredentials | None'] = relationship(
        back_populates='user', uselist=False, cascade='all, delete-orphan',
    )

    __table_args__ = (
        Index('ix_auth_users_status', 'status'),
        Index('ix_auth_users_profile_id', 'profile_id'),
    )
```

## Repository helpers (`shared/db/repositories/auth.py`)

Funciones puras sobre `Session`:

```python
def get_user_by_email(session: Session, email: str) -> AuthUser | None: ...
def create_pending_user(session: Session, *, email: str) -> AuthUser: ...
def mark_user_active(session: Session, user: AuthUser) -> None: ...
def increment_failed_attempts(session: Session, user: AuthUser) -> int: ...
def reset_failed_attempts(session: Session, user: AuthUser) -> None: ...
def lock_user(session: Session, user: AuthUser, until: datetime) -> None: ...

def insert_email_code(
    session: Session, *, user_id: UUID, code_hash: bytes,
    kind: AuthCodeKind, expires_at: datetime,
) -> AuthEmailCode: ...
def consume_email_code(
    session: Session, *, user_id: UUID, kind: AuthCodeKind, code_hash: bytes,
) -> AuthEmailCode | None:  # increments attempts, returns row if hash match + not expired
    ...

def insert_magic_link(...) -> AuthMagicLink: ...
def consume_magic_link(session, *, token_hash: bytes) -> AuthMagicLink | None: ...

def insert_audit_event(
    session: Session, *, event: str, success: bool, user_id: UUID | None = None,
    error_code: str | None = None, ip: str | None = None,
    user_agent: str | None = None, niche: str | None = None,
    metadata: dict | None = None,
) -> None: ...
```

## Indices y queries planeadas

| Query | Endpoint | Indice |
|-------|----------|--------|
| `SELECT ... FROM auth_users WHERE email = ?` | register.start, login.start | UNIQUE constraint sobre `email` (auto) |
| `SELECT ... FROM auth_email_codes WHERE user_id = ? AND kind = ? AND consumed_at IS NULL ORDER BY created_at DESC LIMIT 1` | verify-code | `ix_auth_email_codes_user_kind` |
| `SELECT ... FROM auth_magic_links WHERE token_hash = ? AND consumed_at IS NULL` | verify-magic-link | UNIQUE constraint sobre `token_hash` (auto) |
| `INSERT INTO auth_audit_log ...` | siempre | n/a (insert-only) |

## Que se VERIFICA contra el ER diagram general

- `cv_profiles.id` queda intacto. La FK `auth_users.profile_id` agrega
  una relacion opcional 0..1 -> 1.
- No se introducen rupturas en relaciones existentes
  (`cv_profile_niches`, `cv_profile_stats`, etc.).
- El `down_revision = '00000001'` (la migration inicial).

## Update al ER permanente

Al finalizar el plan, agregar el cluster `auth_*` al
`docs/diagrams/db-er.mmd` para mantener la fuente de verdad sincronizada.
Esta tarea es parte del commit final de la fase 1.
