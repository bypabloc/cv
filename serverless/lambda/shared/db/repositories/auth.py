"""@module repositories.auth — helpers de queries del dominio auth.

Funciones puras sobre `Session` (no abren transactions, eso lo controla
el caller). Los services del Lambda `auth` y `auth_email_worker` los
consumen via `from shared.db.repositories.auth import ...`.

Convencion de retorno:
- `get_user_by_email`, `consume_email_code`, `consume_magic_link`
  retornan el modelo o `None` si no existe / expired / consumed.
- `create_pending_user`, `insert_email_code`, `insert_magic_link`
  retornan el modelo recien insertado.
- Mutaciones (`mark_user_active`, `lock_user`, ...) retornan `None` —
  modifican el modelo in-place.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from shared.db.models.auth import (
    AuthAuditLog,
    AuthCodeKind,
    AuthCredentials,
    AuthEmailCode,
    AuthLinkKind,
    AuthMagicLink,
    AuthUser,
    AuthUserStatus,
)

__all__ = [
    'consume_email_code',
    'consume_magic_link',
    'create_pending_user',
    'get_last_email_code',
    'get_magic_link_state',
    'get_user_by_email',
    'increment_failed_attempts',
    'insert_audit_event',
    'insert_email_code',
    'insert_magic_link',
    'invalidate_active_codes_and_links',
    'lock_user',
    'mark_user_active',
    'reset_failed_attempts',
    'set_password_hash',
    'update_last_login',
]


# ----- Users -----


def get_user_by_email(session: Session, email: str) -> AuthUser | None:
    """Lookup case-insensitive (la columna es CITEXT).

    El caller deberia normalizar el email a lower() + strip() antes,
    pero CITEXT garantiza la insensibilidad incluso si no lo hace.
    """
    stmt = select(AuthUser).where(AuthUser.email == email)
    return session.execute(stmt).scalar_one_or_none()


def create_pending_user(session: Session, *, email: str) -> AuthUser:
    """Crea un row con status=pending. El caller llama session.flush()
    (o session.commit()) para que el `id` autogenerado este disponible.
    """
    user = AuthUser(email=email, status=AuthUserStatus.PENDING)
    session.add(user)
    session.flush()
    return user


def mark_user_active(
    session: Session, user: AuthUser, *, when: datetime | None = None,
) -> None:
    """Cambia status a `active` y setea `email_verified_at`."""
    user.status = AuthUserStatus.ACTIVE
    user.email_verified_at = when or datetime.now(tz=user.created_at.tzinfo)
    user.failed_attempts = 0
    session.flush()


def increment_failed_attempts(
    session: Session, user: AuthUser,
) -> int:
    """Incrementa el contador. Retorna el valor nuevo."""
    user.failed_attempts = (user.failed_attempts or 0) + 1
    session.flush()
    return user.failed_attempts


def reset_failed_attempts(session: Session, user: AuthUser) -> None:
    """Resetea a 0 (tras login exitoso)."""
    user.failed_attempts = 0
    session.flush()


def lock_user(
    session: Session, user: AuthUser, *, until: datetime,
) -> None:
    """Cambia status a `locked` y setea `locked_until`."""
    user.status = AuthUserStatus.LOCKED
    user.locked_until = until
    session.flush()


def update_last_login(
    session: Session,
    user: AuthUser,
    *,
    when: datetime | None = None,
) -> None:
    """Setea `last_login_at` + resetea `failed_attempts` (AC-22).

    Lo llaman los controllers `login/verify_magic_link` y
    `login/verify_code` tras un login exitoso.
    """
    user.last_login_at = when or datetime.now(tz=user.created_at.tzinfo)
    user.failed_attempts = 0
    session.flush()


def invalidate_active_codes_and_links(
    session: Session,
    *,
    user_id: str,
    kind_code: AuthCodeKind,
    kind_link: AuthLinkKind,
    when: datetime | None = None,
) -> None:
    """Marca consumed_at=now en codes y magic_links activos del user (AC-19).

    Usado por `register.start` cuando el visitante reinicia el flow:
    invalida los artefactos pendientes para que solo el ultimo par
    code+link sea valido. NO toca rows consumed_at!=None.
    """
    now = when or datetime.now(tz=UTC)
    # Codes activos
    codes_stmt = select(AuthEmailCode).where(
        AuthEmailCode.user_id == user_id,
        AuthEmailCode.kind == kind_code,
        AuthEmailCode.consumed_at.is_(None),
    )
    for row in session.execute(codes_stmt).scalars():
        row.consumed_at = now
    # Magic links activos
    links_stmt = select(AuthMagicLink).where(
        AuthMagicLink.user_id == user_id,
        AuthMagicLink.kind == kind_link,
        AuthMagicLink.consumed_at.is_(None),
    )
    for row in session.execute(links_stmt).scalars():
        row.consumed_at = now
    session.flush()


# ----- Credentials -----


def set_password_hash(
    session: Session, *, user_id: str, password_hash: str,
    algo: str = 'argon2id',
) -> AuthCredentials:
    """Upsert del hash de password (1-to-0..1)."""
    existing = session.get(AuthCredentials, user_id)
    if existing is None:
        cred = AuthCredentials(
            user_id=user_id, password_hash=password_hash, algo=algo,
        )
        session.add(cred)
        session.flush()
        return cred
    existing.password_hash = password_hash
    existing.algo = algo
    session.flush()
    return existing


# ----- Email codes -----


def insert_email_code(
    session: Session,
    *,
    user_id: str,
    code_hash: bytes,
    kind: AuthCodeKind,
    expires_at: datetime,
) -> AuthEmailCode:
    """Inserta un code nuevo. NO consume codes anteriores."""
    code = AuthEmailCode(
        user_id=user_id,
        code_hash=code_hash,
        kind=kind,
        expires_at=expires_at,
    )
    session.add(code)
    session.flush()
    return code


def get_last_email_code(
    session: Session,
    *,
    user_id: str,
    kind: AuthCodeKind,
) -> AuthEmailCode | None:
    """Devuelve el ultimo `auth_email_codes` emitido para (user, kind).

    NO filtra por `consumed_at`: lo usa el throttle de
    `verify.resend-code` que mide `now - created_at` del ultimo code
    (consumed o no) para evitar abuso del endpoint (AC-21).
    """
    stmt = (
        select(AuthEmailCode)
        .where(
            AuthEmailCode.user_id == user_id,
            AuthEmailCode.kind == kind,
        )
        .order_by(AuthEmailCode.created_at.desc())
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


def consume_email_code(
    session: Session,
    *,
    user_id: str,
    kind: AuthCodeKind,
    code_hash: bytes,
) -> AuthEmailCode | None:
    """Busca el code activo (`consumed_at IS NULL`) que matchea.

    Retorna el row si:
    - hay un row activo para `(user_id, kind)`,
    - el `code_hash` coincide,
    - `expires_at > now`.

    En caso afirmativo, marca `consumed_at = now` y retorna el row.

    Si hay un row activo pero el code es WRONG, incrementa
    `attempts` y retorna None. El caller debe decidir si llamar
    `lock_user` cuando attempts >= 5.
    """
    stmt = (
        select(AuthEmailCode)
        .where(
            AuthEmailCode.user_id == user_id,
            AuthEmailCode.kind == kind,
            AuthEmailCode.consumed_at.is_(None),
        )
        .order_by(AuthEmailCode.created_at.desc())
        .limit(1)
    )
    row = session.execute(stmt).scalar_one_or_none()
    if row is None:
        return None
    now = datetime.now(tz=row.created_at.tzinfo)
    if row.expires_at <= now:
        return None
    if row.code_hash != code_hash:
        row.attempts += 1
        session.flush()
        return None
    row.consumed_at = now
    session.flush()
    return row


# ----- Magic links -----


def insert_magic_link(
    session: Session,
    *,
    user_id: str,
    token_hash: bytes,
    kind: AuthLinkKind,
    expires_at: datetime,
    ip: str | None = None,
    user_agent: str | None = None,
) -> AuthMagicLink:
    """Inserta un magic-link nuevo."""
    link = AuthMagicLink(
        user_id=user_id,
        token_hash=token_hash,
        kind=kind,
        expires_at=expires_at,
        ip=ip,
        user_agent=user_agent,
    )
    session.add(link)
    session.flush()
    return link


def get_magic_link_state(
    session: Session, *, token_hash: bytes,
) -> AuthMagicLink | None:
    """Devuelve el row sin consumirlo. Para distinguir consumed/expired.

    Usado por los controllers `verify_magic_link` para devolver el codigo
    de error correcto (LINK_CONSUMED vs LINK_EXPIRED) cuando
    `consume_magic_link` retorna `None`.
    """
    stmt = select(AuthMagicLink).where(AuthMagicLink.token_hash == token_hash)
    return session.execute(stmt).scalar_one_or_none()


def consume_magic_link(
    session: Session, *, token_hash: bytes,
) -> AuthMagicLink | None:
    """Busca por `token_hash` (UNIQUE).

    Retorna el row si:
    - existe,
    - `consumed_at IS NULL`,
    - `expires_at > now`.

    Marca `consumed_at = now` y retorna. En cualquier otro caso (no
    existe, ya consumido, expirado), retorna None — el caller distingue
    el error consultando con `_get_magic_link_state` si necesita
    diferenciar.

    Para diferenciar "consumed" vs "expired" vs "no existe" el caller
    debe hacer un segundo select sin filtros antes de consumir.
    """
    stmt = select(AuthMagicLink).where(AuthMagicLink.token_hash == token_hash)
    row = session.execute(stmt).scalar_one_or_none()
    if row is None:
        return None
    if row.consumed_at is not None:
        return None
    now = datetime.now(tz=row.created_at.tzinfo)
    if row.expires_at <= now:
        return None
    row.consumed_at = now
    session.flush()
    return row


# ----- Audit log -----


def insert_audit_event(
    session: Session,
    *,
    event: str,
    success: bool,
    user_id: str | None = None,
    error_code: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    niche: str | None = None,
    meta_data: dict[str, Any] | None = None,
) -> AuthAuditLog:
    """Inserta un row de auditoria. NO devuelve por default (insert-only)."""
    row = AuthAuditLog(
        event=event,
        success=success,
        user_id=user_id,
        error_code=error_code,
        ip=ip,
        user_agent=user_agent,
        niche=niche,
        meta_data=meta_data,
    )
    session.add(row)
    session.flush()
    return row
