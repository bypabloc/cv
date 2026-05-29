"""@module repositories.auth_mfa — helpers de queries del dominio MFA + WebAuthn.

Funciones puras sobre `Session` (no abren transactions, eso lo controla
el caller). Los services del Lambda `auth` las consumen via
`from shared.db.repositories.auth_mfa import ...`.

Cubre 3 tablas (plan 02): `auth_mfa_methods`, `auth_mfa_recovery_codes`,
`auth_webauthn_credentials`. La cuenta `count_active_mfa` es
TRANSVERSAL (suma metodos confirmados activos + passkeys activos) —
alimenta el guard MUST_KEEP_ONE_MFA_METHOD (AC-5 / AC-17).
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from shared.db.models import (
    AuthMfaKind,
    AuthMfaMethod,
    AuthMfaRecoveryCode,
    AuthWebauthnCredential,
)

__all__ = [
    'confirm_mfa',
    'consume_recovery_code',
    'count_active_mfa',
    'delete_webauthn_credential',
    'disable_mfa',
    'disable_webauthn_credential',
    'get_mfa_method',
    'get_webauthn_credential_by_id',
    'get_webauthn_credentials',
    'insert_recovery_codes',
    'insert_webauthn_credential',
    'list_mfa_methods',
    'mark_method_used',
    'regenerate_recovery_codes',
    'set_preferred',
    'update_sign_count',
    'upsert_totp_method',
]


def _now(when: datetime | None) -> datetime:
    return when or datetime.now(tz=UTC)


# ----- MFA methods -----


def list_mfa_methods(
    session: Session, *, user_id: str,
) -> list[AuthMfaMethod]:
    """Metodos MFA activos del user (`disabled_at IS NULL`)."""
    stmt = select(AuthMfaMethod).where(
        AuthMfaMethod.user_id == user_id,
        AuthMfaMethod.disabled_at.is_(None),
    )
    return list(session.execute(stmt).scalars())


def get_mfa_method(
    session: Session, *, user_id: str, kind: AuthMfaKind,
) -> AuthMfaMethod | None:
    """El row `(user_id, kind)` (UNIQUE) o None."""
    stmt = select(AuthMfaMethod).where(
        AuthMfaMethod.user_id == user_id,
        AuthMfaMethod.kind == kind,
    )
    return session.execute(stmt).scalar_one_or_none()


def upsert_totp_method(
    session: Session, *, user_id: str, ciphertext: bytes,
) -> AuthMfaMethod:
    """INSERT (o reusa) un row TOTP pendiente (`confirmed_at=NULL`).

    Si ya existe un row TOTP (re-setup), reescribe el ciphertext y
    resetea `confirmed_at`/`disabled_at` para re-confirmar.
    """
    existing = get_mfa_method(
        session, user_id=user_id, kind=AuthMfaKind.TOTP,
    )
    if existing is not None:
        existing.totp_secret_ciphertext = ciphertext
        existing.confirmed_at = None
        existing.disabled_at = None
        session.flush()
        return existing
    method = AuthMfaMethod(
        user_id=user_id,
        kind=AuthMfaKind.TOTP,
        totp_secret_ciphertext=ciphertext,
    )
    session.add(method)
    session.flush()
    return method


def confirm_mfa(
    session: Session, *, user_id: str, kind: AuthMfaKind,
    when: datetime | None = None,
) -> AuthMfaMethod | None:
    """Marca `confirmed_at=now()` en el row `(user_id, kind)`. None si no existe."""
    method = get_mfa_method(session, user_id=user_id, kind=kind)
    if method is None:
        return None
    method.confirmed_at = _now(when)
    method.disabled_at = None
    session.flush()
    return method


def disable_mfa(
    session: Session, *, user_id: str, kind: AuthMfaKind,
    when: datetime | None = None,
) -> bool:
    """Marca `disabled_at=now()` en el row `(user_id, kind)`. False si no existe."""
    method = get_mfa_method(session, user_id=user_id, kind=kind)
    if method is None:
        return False
    method.disabled_at = _now(when)
    method.preferred = False
    session.flush()
    return True


def set_preferred(
    session: Session, *, user_id: str, kind: AuthMfaKind,
) -> None:
    """`preferred=True` en el row `(user_id, kind)`, `False` en los demas."""
    for method in list_mfa_methods(session, user_id=user_id):
        method.preferred = method.kind == kind
    session.flush()


def mark_method_used(
    session: Session, *, user_id: str, kind: AuthMfaKind,
    when: datetime | None = None,
) -> None:
    """Setea `last_used_at=now()` en el metodo usado (login con TOTP)."""
    method = get_mfa_method(session, user_id=user_id, kind=kind)
    if method is not None:
        method.last_used_at = _now(when)
        session.flush()


def count_active_mfa(session: Session, *, user_id: str) -> int:
    """Cuenta TRANSVERSAL de metodos MFA activos del user.

    `auth_mfa_methods` confirmados y no deshabilitados +
    `auth_webauthn_credentials` no deshabilitados. Es la base del guard
    MUST_KEEP_ONE_MFA_METHOD (AC-5 y AC-17).
    """
    methods = session.scalar(
        select(func.count())
        .select_from(AuthMfaMethod)
        .where(
            AuthMfaMethod.user_id == user_id,
            AuthMfaMethod.confirmed_at.is_not(None),
            AuthMfaMethod.disabled_at.is_(None),
        )
    )
    passkeys = session.scalar(
        select(func.count())
        .select_from(AuthWebauthnCredential)
        .where(
            AuthWebauthnCredential.user_id == user_id,
            AuthWebauthnCredential.disabled_at.is_(None),
        )
    )
    return int(methods or 0) + int(passkeys or 0)


# ----- Recovery codes -----


def insert_recovery_codes(
    session: Session, *, user_id: str, code_hashes: list[bytes],
) -> None:
    """Inserta un row por hash de recovery code."""
    for code_hash in code_hashes:
        session.add(
            AuthMfaRecoveryCode(user_id=user_id, code_hash=code_hash),
        )
    session.flush()


def consume_recovery_code(
    session: Session, *, user_id: str, code_hash: bytes,
    when: datetime | None = None,
) -> bool:
    """Marca `consumed_at=now()` en el code activo que matchea. False si no hay.

    Filtra `consumed_at IS NULL`: un code ya consumido NO matchea
    (devuelve False).
    """
    stmt = select(AuthMfaRecoveryCode).where(
        AuthMfaRecoveryCode.user_id == user_id,
        AuthMfaRecoveryCode.code_hash == code_hash,
        AuthMfaRecoveryCode.consumed_at.is_(None),
    )
    row = session.execute(stmt).scalar_one_or_none()
    if row is None:
        return False
    row.consumed_at = _now(when)
    session.flush()
    return True


def regenerate_recovery_codes(
    session: Session, *, user_id: str, code_hashes: list[bytes],
) -> None:
    """Borra TODOS los recovery codes del user e inserta los nuevos."""
    session.execute(
        delete(AuthMfaRecoveryCode).where(
            AuthMfaRecoveryCode.user_id == user_id,
        )
    )
    insert_recovery_codes(session, user_id=user_id, code_hashes=code_hashes)


# ----- WebAuthn credentials -----


def insert_webauthn_credential(
    session: Session,
    *,
    user_id: str,
    credential_id: bytes,
    public_key: bytes,
    sign_count: int,
    transports: object | None,
    attestation_format: str | None,
    aaguid: str | None,
    nickname: str | None,
) -> AuthWebauthnCredential:
    """Inserta un credential WebAuthn nuevo."""
    cred = AuthWebauthnCredential(
        user_id=user_id,
        credential_id=credential_id,
        public_key=public_key,
        sign_count=sign_count,
        transports=transports,
        attestation_format=attestation_format,
        aaguid=aaguid,
        nickname=nickname,
    )
    session.add(cred)
    session.flush()
    return cred


def get_webauthn_credentials(
    session: Session, *, user_id: str,
) -> list[AuthWebauthnCredential]:
    """Credentials activos del user, ordenados por `last_used_at` DESC."""
    stmt = (
        select(AuthWebauthnCredential)
        .where(
            AuthWebauthnCredential.user_id == user_id,
            AuthWebauthnCredential.disabled_at.is_(None),
        )
        .order_by(AuthWebauthnCredential.last_used_at.desc())
    )
    return list(session.execute(stmt).scalars())


def get_webauthn_credential_by_id(
    session: Session, *, credential_id: bytes,
) -> AuthWebauthnCredential | None:
    """Lookup por el `credential_id` (BYTEA UK) emitido por el authenticator."""
    stmt = select(AuthWebauthnCredential).where(
        AuthWebauthnCredential.credential_id == credential_id,
    )
    return session.execute(stmt).scalar_one_or_none()


def update_sign_count(
    session: Session, *, credential_id: bytes, new_count: int,
    when: datetime | None = None,
) -> bool:
    """Actualiza `sign_count` SOLO si `new_count > stored` (monotonico).

    Devuelve False si el credential no existe o si el counter no avanzo
    (defensa adicional; la clone detection ya corre en `shared.auth`).
    """
    cred = get_webauthn_credential_by_id(
        session, credential_id=credential_id,
    )
    if cred is None or new_count <= cred.sign_count:
        return False
    cred.sign_count = new_count
    cred.last_used_at = _now(when)
    session.flush()
    return True


def disable_webauthn_credential(
    session: Session, *, credential_id: bytes,
    when: datetime | None = None,
) -> None:
    """Marca `disabled_at=now()` (clone detection — AC-15)."""
    cred = get_webauthn_credential_by_id(
        session, credential_id=credential_id,
    )
    if cred is not None:
        cred.disabled_at = _now(when)
        session.flush()


def delete_webauthn_credential(
    session: Session, *, user_id: str, record_id: str,
) -> bool:
    """Borra el credential del user por su `id` (UUID PK). False si no existe.

    Filtra por `user_id` ademas del `id`: un `record_id` de OTRO user NO
    matchea -> False (el controller devuelve 404, anti-enumeration AC-25).
    """
    stmt = select(AuthWebauthnCredential).where(
        AuthWebauthnCredential.user_id == user_id,
        AuthWebauthnCredential.id == record_id,
    )
    cred = session.execute(stmt).scalar_one_or_none()
    if cred is None:
        return False
    session.delete(cred)
    session.flush()
    return True
