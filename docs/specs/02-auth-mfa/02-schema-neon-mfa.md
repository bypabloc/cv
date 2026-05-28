# 02. Schema Neon — extension `auth_mfa_*` + `auth_webauthn_credentials`

## ER ASCII (delta sobre plan 01)

```text
auth_users
─────────────
 id  uuid PK
 email citext
 status auth_user_status
 ...
   |
   | 1
   ├──────────────────────────┬──────────────────────────┬──────────────────────┐
   | 0..*                     | 0..*                     | 0..*                 | (de plan 01)
   v                          v                          v                      v
auth_mfa_methods    auth_mfa_recovery_codes    auth_webauthn_credentials   auth_credentials
───────────────     ─────────────────────       ──────────────────────       (ya existe)
 id  uuid PK         id  uuid PK                 id              uuid PK
 user_id  uuid FK    user_id uuid FK             user_id         uuid FK
 kind  mfa_kind      code_hash bytea UK          credential_id   bytea UK
 preferred  bool     consumed_at ts NULL         public_key      bytea
 confirmed_at ts     created_at  ts              sign_count      int default 0
 disabled_at ts                                  transports      jsonb
 last_used_at ts                                 attestation_format varchar
 -- TOTP-only:                                   aaguid          uuid NULL
 totp_secret_ciphertext bytea NULL               nickname        varchar
 totp_algorithm   varchar NULL                   created_at      ts
 totp_digits      int NULL  (default 6)          last_used_at    ts NULL
 totp_period      int NULL  (default 30)         disabled_at     ts NULL
 created_at  ts
```

## Migration 00000003

```python
"""auth_mfa

Revision ID: 00000003
Revises: 00000002
Create Date: 2026-05-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '00000003'
down_revision = '00000002'


def upgrade() -> None:
    mfa_kind = postgresql.ENUM('totp', 'email_code', name='auth_mfa_kind')
    mfa_kind.create(op.get_bind())

    op.create_table(
        'auth_mfa_methods',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuidv7()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('kind', mfa_kind, nullable=False),
        sa.Column('preferred', sa.Boolean(), nullable=False,
                  server_default=sa.text('false')),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('disabled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('totp_secret_ciphertext', postgresql.BYTEA(), nullable=True,
                  comment='kms:Encrypt output (CMK alias/portfolio-lambdas + EncryptionContext={user_id, purpose:totp}). Sin nonce — KMS lo gestiona internamente.'),
        sa.Column('totp_algorithm', sa.String(16), nullable=True,
                  server_default='SHA1'),
        sa.Column('totp_digits', sa.Integer(), nullable=True,
                  server_default='6'),
        sa.Column('totp_period', sa.Integer(), nullable=True,
                  server_default='30'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['auth_users.id'],
                                ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'kind', name='uq_auth_mfa_user_kind'),
    )
    op.create_index('ix_auth_mfa_methods_user', 'auth_mfa_methods', ['user_id'])

    op.create_table(
        'auth_mfa_recovery_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuidv7()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code_hash', postgresql.BYTEA(), nullable=False, unique=True),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['auth_users.id'],
                                ondelete='CASCADE'),
    )
    op.create_index('ix_auth_mfa_recovery_user_active',
                    'auth_mfa_recovery_codes', ['user_id', 'consumed_at'])

    op.create_table(
        'auth_webauthn_credentials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('uuidv7()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('credential_id', postgresql.BYTEA(), nullable=False, unique=True),
        sa.Column('public_key', postgresql.BYTEA(), nullable=False),
        sa.Column('sign_count', sa.Integer(), nullable=False,
                  server_default='0'),
        sa.Column('transports', postgresql.JSONB(), nullable=True),
        sa.Column('attestation_format', sa.String(32), nullable=True),
        sa.Column('aaguid', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('nickname', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('disabled_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['auth_users.id'],
                                ondelete='CASCADE'),
    )
    op.create_index('ix_webauthn_credentials_user', 'auth_webauthn_credentials',
                    ['user_id', 'disabled_at'])


def downgrade() -> None:
    op.drop_table('auth_webauthn_credentials')
    op.drop_table('auth_mfa_recovery_codes')
    op.drop_table('auth_mfa_methods')
    op.execute('DROP TYPE IF EXISTS auth_mfa_kind')
```

## Modelos SQLAlchemy

```text
serverless/lambda/shared/db/models/auth/
├── mfa_method.py            # AuthMfaMethod
├── recovery_code.py         # AuthMfaRecoveryCode
└── webauthn_credential.py   # AuthWebauthnCredential
```

```python
# mfa_method.py
class AuthMfaMethod(UUIDPKMixin, Base):
    __tablename__ = 'auth_mfa_methods'

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey('auth_users.id', ondelete='CASCADE'), nullable=False)
    kind: Mapped[AuthMfaKind] = mapped_column(
        PgEnum(AuthMfaKind, name='auth_mfa_kind'), nullable=False)
    preferred: Mapped[bool] = mapped_column(default=False, nullable=False)
    confirmed_at: Mapped[datetime | None]
    disabled_at: Mapped[datetime | None]
    last_used_at: Mapped[datetime | None]

    # TOTP-only campos (NULL para email_code). El ciphertext es la
    # salida de `kms:Encrypt` con la CMK `alias/portfolio-lambdas` +
    # `EncryptionContext={user_id, purpose:totp}`. NO envelope
    # encryption — sin nonce, sin data_key. Ver `.claude/rules/
    # serverless-secrets.md` y la decision 1 del README del plan.
    totp_secret_ciphertext: Mapped[bytes | None]
    totp_algorithm: Mapped[str | None] = mapped_column(default='SHA1')
    totp_digits: Mapped[int | None] = mapped_column(default=6)
    totp_period: Mapped[int | None] = mapped_column(default=30)

    created_at: Mapped[datetime] = mapped_column(
        server_default=sa.text('now()'), nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'kind', name='uq_auth_mfa_user_kind'),
        Index('ix_auth_mfa_methods_user', 'user_id'),
    )
```

## Repository extensions

`shared/db/repositories/auth_mfa.py`:

```python
def list_mfa_methods(session, *, user_id) -> list[AuthMfaMethod]: ...
def get_mfa_method(session, *, user_id, kind) -> AuthMfaMethod | None: ...
def upsert_totp_method(session, *, user_id, ciphertext: bytes) -> AuthMfaMethod: ...
def confirm_mfa(session, *, method_id) -> None: ...
def count_active_mfa(session, *, user_id) -> int:
    """Cuenta transversal: auth_mfa_methods activos (confirmed_at NOT NULL,
    disabled_at NULL) + auth_webauthn_credentials activos (disabled_at NULL).
    Usada por AC-5 y AC-17 para validar MUST_KEEP_ONE_MFA_METHOD."""
def disable_mfa(session, *, user_id, kind) -> None: ...
def set_preferred(session, *, user_id, kind) -> None: ...

def insert_recovery_codes(session, *, user_id, code_hashes: list[bytes]) -> None: ...
def consume_recovery_code(session, *, user_id, code_hash) -> bool: ...
def regenerate_recovery_codes(session, *, user_id) -> None: ...

def insert_webauthn_credential(session, *, user_id, credential_id, public_key,
                                transports, attestation_format, aaguid, nickname) -> ...: ...
def get_webauthn_credentials(session, *, user_id) -> list[AuthWebauthnCredential]: ...
def get_webauthn_credential_by_id(session, *, credential_id: bytes) -> AuthWebauthnCredential | None: ...
def update_sign_count(session, *, credential_id, new_count) -> None: ...
def delete_webauthn_credential(session, *, user_id, credential_id) -> bool: ...
```

## Indices justificacion

| Indice | Justificacion |
|--------|---------------|
| `uq_auth_mfa_user_kind` | Un user no puede tener 2 TOTP a la vez (o 2 email_code) |
| `ix_auth_mfa_methods_user` | Lookup en cada login con MFA: `SELECT ... WHERE user_id = ? AND disabled_at IS NULL` |
| `ix_auth_mfa_recovery_user_active` | `... WHERE user_id = ? AND consumed_at IS NULL` |
| `auth_webauthn_credentials.credential_id` UNIQUE | Lookup por credential_id en login-verify |
| `ix_webauthn_credentials_user` | Listar credentials del user activos |

## Update al ER permanente

Al cerrar plan 02: actualizar `docs/diagrams/db-er.mmd` con las 3
tablas nuevas + relacion FK.
