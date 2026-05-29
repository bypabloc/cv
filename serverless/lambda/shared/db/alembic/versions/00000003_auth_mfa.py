"""auth_mfa

Revision ID: 00000003
Revises: 00000002
Create Date: 2026-05-28

Extension MFA + WebAuthn del dominio auth (plan 02-auth-mfa). Agrega:

- enum PG `auth_mfa_kind` ('totp', 'email_code').
- columna `auth_users.sessions_revoked_at` (epoch de revocacion de
  sesiones — AC-27; al confirmar el primer MFA se setea a now() y
  `session.refresh` rechaza refreshes anteriores).
- tabla `auth_mfa_methods`     (TOTP secret cifrado con KMS CMK directa).
- tabla `auth_mfa_recovery_codes` (10 codes por user, hash SHA-256).
- tabla `auth_webauthn_credentials` (passkeys: credential_id UK, public
  key CBOR, sign_count monotonico para clone detection).

Decisiones:
- `totp_secret_ciphertext` es la salida de `kms:Encrypt` (CMK directa,
  EncryptionContext={user_id, purpose:totp}); SIN nonce ni data_key
  (decision 1). El secret en plain NUNCA se persiste.
- WebAuthn challenges NO viven aqui: son efimeros (TTL 5 min) y van a
  DynamoDB `portfolio-webauthn-challenges-${stage}` (decision 5).
- forward-only en prod: el downgrade tira `auth_webauthn_credentials`
  que puede tener data real (decision 11) — NO se corre en prod.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '00000003'
down_revision: str | None = '00000002'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- ENUM auth_mfa_kind ---
    op.execute("CREATE TYPE auth_mfa_kind AS ENUM ('totp', 'email_code')")
    auth_mfa_kind_enum = postgresql.ENUM(
        'totp', 'email_code', name='auth_mfa_kind', create_type=False,
    )

    # --- auth_users.sessions_revoked_at (AC-27) ---
    op.add_column(
        'auth_users',
        sa.Column(
            'sessions_revoked_at', sa.DateTime(timezone=True), nullable=True,
        ),
    )

    # --- auth_mfa_methods ---
    op.create_table(
        'auth_mfa_methods',
        sa.Column(
            'id', sa.UUID(as_uuid=False),
            server_default=sa.text('uuidv7()'), nullable=False,
        ),
        sa.Column('user_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('kind', auth_mfa_kind_enum, nullable=False),
        sa.Column(
            'preferred', sa.Boolean(),
            server_default=sa.text('false'), nullable=False,
        ),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('disabled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('totp_secret_ciphertext', postgresql.BYTEA(), nullable=True),
        sa.Column(
            'totp_algorithm', sa.String(length=16),
            server_default=sa.text("'SHA1'"), nullable=True,
        ),
        sa.Column(
            'totp_digits', sa.Integer(),
            server_default=sa.text('6'), nullable=True,
        ),
        sa.Column(
            'totp_period', sa.Integer(),
            server_default=sa.text('30'), nullable=True,
        ),
        sa.Column(
            'created_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['auth_users.id'],
            name=op.f('fk_auth_mfa_methods_user_id_auth_users'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_auth_mfa_methods')),
        sa.UniqueConstraint(
            'user_id', 'kind', name='uq_auth_mfa_user_kind',
        ),
    )
    op.create_index(
        'ix_auth_mfa_methods_user', 'auth_mfa_methods', ['user_id'],
    )

    # --- auth_mfa_recovery_codes ---
    op.create_table(
        'auth_mfa_recovery_codes',
        sa.Column(
            'id', sa.UUID(as_uuid=False),
            server_default=sa.text('uuidv7()'), nullable=False,
        ),
        sa.Column('user_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('code_hash', postgresql.BYTEA(), nullable=False),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['auth_users.id'],
            name=op.f('fk_auth_mfa_recovery_codes_user_id_auth_users'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint(
            'id', name=op.f('pk_auth_mfa_recovery_codes'),
        ),
        sa.UniqueConstraint(
            'code_hash', name='uq_auth_mfa_recovery_codes_code_hash',
        ),
    )
    op.create_index(
        'ix_auth_mfa_recovery_user_active', 'auth_mfa_recovery_codes',
        ['user_id', 'consumed_at'],
    )

    # --- auth_webauthn_credentials ---
    op.create_table(
        'auth_webauthn_credentials',
        sa.Column(
            'id', sa.UUID(as_uuid=False),
            server_default=sa.text('uuidv7()'), nullable=False,
        ),
        sa.Column('user_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('credential_id', postgresql.BYTEA(), nullable=False),
        sa.Column('public_key', postgresql.BYTEA(), nullable=False),
        sa.Column(
            'sign_count', sa.Integer(),
            server_default=sa.text('0'), nullable=False,
        ),
        sa.Column('transports', postgresql.JSONB(), nullable=True),
        sa.Column('attestation_format', sa.String(length=32), nullable=True),
        sa.Column('aaguid', sa.UUID(as_uuid=False), nullable=True),
        sa.Column('nickname', sa.String(length=64), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('disabled_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ['user_id'], ['auth_users.id'],
            name=op.f('fk_auth_webauthn_credentials_user_id_auth_users'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint(
            'id', name=op.f('pk_auth_webauthn_credentials'),
        ),
        sa.UniqueConstraint(
            'credential_id',
            name='uq_auth_webauthn_credentials_credential_id',
        ),
    )
    op.create_index(
        'ix_webauthn_credentials_user', 'auth_webauthn_credentials',
        ['user_id', 'disabled_at'],
    )


def downgrade() -> None:
    op.drop_index(
        'ix_webauthn_credentials_user',
        table_name='auth_webauthn_credentials',
    )
    op.drop_table('auth_webauthn_credentials')
    op.drop_index(
        'ix_auth_mfa_recovery_user_active',
        table_name='auth_mfa_recovery_codes',
    )
    op.drop_table('auth_mfa_recovery_codes')
    op.drop_index('ix_auth_mfa_methods_user', table_name='auth_mfa_methods')
    op.drop_table('auth_mfa_methods')
    op.drop_column('auth_users', 'sessions_revoked_at')
    op.execute('DROP TYPE IF EXISTS auth_mfa_kind')
