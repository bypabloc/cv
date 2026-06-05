"""@module repositories.auth_users — queries de gestion de usuarios (plan 03).

Helpers de la operacion `users` (profile / status / admin) + el session
tracking que inyecta el Lambda `auth`. Separa estos helpers de
`repositories/auth.py` (ciclo de autenticacion del plan 01).

Convencion (igual que `auth.py` / `auth_mfa.py`):
- `session: Session` es el PRIMER arg posicional; el resto keyword-only.
- getters/consumers -> model | None; inserts -> el model nuevo;
  mutaciones in-place -> None; ops con resultado binario -> bool;
  listas -> list[...].
- `session.flush()` tras cada mutacion (NUNCA `commit()` — el caller
  posee el `db_session()`).
- IDs de PG son `UUID(as_uuid=False)` -> strings en Python.

GOTCHA — soft-delete NO dispara las FK ON DELETE CASCADE (reaccionan a
DELETE, no a UPDATE) y los modelos auth NO declaran `relationship()`. Por
eso `soft_delete_user` y `hard_delete_user` borran cada tabla hija con un
`delete(Model).where(...)` explicito.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from shared.db.models.auth.admin_action import AuthUserAdminAction
from shared.db.models.auth.audit_log import AuthAuditLog
from shared.db.models.auth.consent_log import AuthUserConsentLog
from shared.db.models.auth.credentials import AuthCredentials
from shared.db.models.auth.email_code import AuthEmailCode
from shared.db.models.auth.enums import AuthLinkKind, AuthUserStatus
from shared.db.models.auth.magic_link import AuthMagicLink
from shared.db.models.auth.mfa_method import AuthMfaMethod
from shared.db.models.auth.recovery_code import AuthMfaRecoveryCode
from shared.db.models.auth.user import AuthUser
from shared.db.models.auth.user_session import AuthUserSession
from shared.db.models.auth.webauthn_credential import AuthWebauthnCredential

__all__ = [
    'consume_email_change_link',
    'count_recovery_codes',
    'count_remaining_recovery_codes',
    'count_user_sessions',
    'count_users',
    'delete_session_by_family',
    'disable_user',
    'enable_user',
    'get_email_change_link',
    'get_password_status',
    'get_session_by_id',
    'get_user_by_id',
    'hard_delete_user',
    'insert_admin_action',
    'insert_consent_log',
    'insert_email_change_link',
    'insert_user_session',
    'list_admin_actions',
    'list_recent_audit',
    'list_user_sessions',
    'list_users_paginated',
    'revoke_all_user_sessions',
    'revoke_session',
    'rotate_session_family_id',
    'soft_delete_user',
    'update_profile',
    'update_session_activity',
    'update_user_email',
]

# Campos de auth_users que `update_profile` puede modificar (whitelist).
_PROFILE_FIELDS = frozenset(
    {
        'display_name',
        'locale',
        'timezone',
        'marketing_consent',
        'privacy_policy_version',
    },
)

# Tablas hijas con FK ON DELETE CASCADE a auth_users.id. El soft-delete
# (UPDATE) NO las dispara, asi que se borran explicito.
_CHILD_MODELS_BY_USER = (
    AuthCredentials,
    AuthMfaMethod,
    AuthMfaRecoveryCode,
    AuthWebauthnCredential,
    AuthEmailCode,
    AuthMagicLink,
)


def _now(when: datetime | None) -> datetime:
    """Devuelve `when` o el `now()` en UTC (mockeable en tests)."""
    return when or datetime.now(tz=UTC)


# ----- Profile -----


def get_user_by_id(session: Session, *, user_id: str) -> AuthUser | None:
    """Lookup del user por PK. None si no existe."""
    return session.get(AuthUser, user_id)


def update_profile(
    session: Session,
    *,
    user_id: str,
    **fields: Any,
) -> AuthUser | None:
    """Actualiza un subset de campos del perfil del user (parcial).

    Solo aplica las keys en `_PROFILE_FIELDS`; ignora el resto. Devuelve
    el user actualizado, o None si no existe.
    """
    user = session.get(AuthUser, user_id)
    if user is None:
        return None
    for key, value in fields.items():
        if key in _PROFILE_FIELDS:
            setattr(user, key, value)
    session.flush()
    return user


def update_user_email(
    session: Session,
    *,
    user_id: str,
    new_email: str,
) -> AuthUser | None:
    """Cambia el email del user (flujo email-change confirmado). None si
    no existe."""
    user = session.get(AuthUser, user_id)
    if user is None:
        return None
    user.email = new_email.strip().lower()
    session.flush()
    return user


def soft_delete_user(
    session: Session,
    *,
    user_id: str,
    anonymized_email: str,
    when: datetime | None = None,
) -> list[str]:
    """Soft-delete del user (UPDATE) + borrado explicito de credenciales.

    Setea `deleted_at` + anonimiza el email, y borra credentials / mfa /
    recovery / webauthn / email_codes / magic_links + las sesiones
    activas. Devuelve los `family_id` de las sesiones borradas para que el
    caller las blackliste en DDB.
    """
    families = list(
        session.execute(
            select(AuthUserSession.family_id).where(
                AuthUserSession.user_id == user_id,
            ),
        ).scalars(),
    )
    for model in _CHILD_MODELS_BY_USER:
        session.execute(delete(model).where(model.user_id == user_id))
    session.execute(
        delete(AuthUserSession).where(AuthUserSession.user_id == user_id),
    )
    user = session.get(AuthUser, user_id)
    if user is not None:
        user.deleted_at = _now(when)
        user.email = anonymized_email
        user.status = AuthUserStatus.DELETED
    session.flush()
    return families


def hard_delete_user(session: Session, *, user_id: str) -> bool:
    """Hard-delete del user con cascada explicita. True si existia.

    Borra credentials / mfa / recovery / webauthn / email_codes /
    magic_links / sessions / consent_log y luego el row de `auth_users`.
    El DELETE del user dispara el `ON DELETE SET NULL` de
    `auth_user_admin_actions` (audit preservado con la referencia en NULL).
    """
    user = session.get(AuthUser, user_id)
    if user is None:
        return False
    for model in _CHILD_MODELS_BY_USER:
        session.execute(delete(model).where(model.user_id == user_id))
    session.execute(
        delete(AuthUserSession).where(AuthUserSession.user_id == user_id),
    )
    session.execute(
        delete(AuthUserConsentLog).where(
            AuthUserConsentLog.user_id == user_id,
        ),
    )
    session.delete(user)
    session.flush()
    return True


def disable_user(session: Session, *, user_id: str) -> bool:
    """Marca status=disabled. False si no existe o ya estaba borrado."""
    user = session.get(AuthUser, user_id)
    if user is None or user.deleted_at is not None:
        return False
    user.status = AuthUserStatus.DISABLED
    session.flush()
    return True


def enable_user(session: Session, *, user_id: str) -> bool:
    """Marca status=active. False si no existe o ya estaba borrado."""
    user = session.get(AuthUser, user_id)
    if user is None or user.deleted_at is not None:
        return False
    user.status = AuthUserStatus.ACTIVE
    session.flush()
    return True


def list_users_paginated(
    session: Session,
    *,
    cursor: str | None = None,
    page_size: int = 50,
    status_filter: str | None = None,
) -> list[AuthUser]:
    """Lista users con paginacion cursor-based (uuidv7 id ASC).

    `WHERE id > cursor [AND status = filter] ORDER BY id ASC LIMIT
    page_size`. uuidv7 ordena cronologicamente, asi que el cursor es el
    `id` del ultimo item de la pagina anterior.
    """
    stmt = select(AuthUser)
    if cursor is not None:
        stmt = stmt.where(AuthUser.id > cursor)
    if status_filter is not None:
        stmt = stmt.where(AuthUser.status == AuthUserStatus(status_filter))
    stmt = stmt.order_by(AuthUser.id.asc()).limit(page_size)
    return list(session.execute(stmt).scalars())


# ----- Session tracking -----


def insert_user_session(
    session: Session,
    *,
    user_id: str,
    family_id: str,
    device_info: dict[str, Any] | None = None,
    ip: str | None = None,
    country: str | None = None,
    user_agent: str | None = None,
) -> AuthUserSession:
    """Inserta una sesion activa (1 por family_id de refresh)."""
    row = AuthUserSession(
        user_id=user_id,
        family_id=family_id,
        device_info=device_info,
        ip=ip,
        country=country,
        user_agent=user_agent,
    )
    session.add(row)
    session.flush()
    return row


def update_session_activity(
    session: Session,
    *,
    family_id: str,
    when: datetime | None = None,
) -> bool:
    """Actualiza `last_active_at` de la sesion de una family. True si existia."""
    row = session.execute(
        select(AuthUserSession).where(
            AuthUserSession.family_id == family_id,
        ),
    ).scalar_one_or_none()
    if row is None:
        return False
    row.last_active_at = _now(when)
    session.flush()
    return True


def rotate_session_family_id(
    session: Session,
    *,
    old_family_id: str,
    new_family_id: str,
    when: datetime | None = None,
) -> bool:
    """Rota el family_id de una sesion (+ bump last_active_at).

    En el refresh actual el family_id se mantiene (old == new), asi que
    esto es un bump de `last_active_at`. Se mantiene generico por si la
    rotation de familia cambia en el futuro. True si la sesion existia.
    """
    row = session.execute(
        select(AuthUserSession).where(
            AuthUserSession.family_id == old_family_id,
        ),
    ).scalar_one_or_none()
    if row is None:
        return False
    row.family_id = new_family_id
    row.last_active_at = _now(when)
    session.flush()
    return True


def list_user_sessions(
    session: Session,
    *,
    user_id: str,
) -> list[AuthUserSession]:
    """Lista las sesiones activas del user, last_active_at DESC."""
    stmt = (
        select(AuthUserSession)
        .where(AuthUserSession.user_id == user_id)
        .order_by(AuthUserSession.last_active_at.desc())
    )
    return list(session.execute(stmt).scalars())


def get_session_by_id(
    session: Session,
    *,
    user_id: str,
    session_id: str,
) -> AuthUserSession | None:
    """Lookup de una sesion por (user_id, id) — dual filter anti-enumeration."""
    return session.execute(
        select(AuthUserSession).where(
            AuthUserSession.user_id == user_id,
            AuthUserSession.id == session_id,
        ),
    ).scalar_one_or_none()


def revoke_session(
    session: Session,
    *,
    user_id: str,
    session_id: str,
) -> str | None:
    """Borra una sesion del user (dual filter). Devuelve su family_id (para
    blacklist) o None si no existe / no es del user."""
    row = get_session_by_id(
        session,
        user_id=user_id,
        session_id=session_id,
    )
    if row is None:
        return None
    family_id = row.family_id
    session.delete(row)
    session.flush()
    return family_id


def delete_session_by_family(session: Session, *, family_id: str) -> bool:
    """Borra la sesion de una family (logout). True si existia.

    Lo usa el session tracking del Lambda `auth` en `session.logout`.
    """
    row = session.execute(
        select(AuthUserSession).where(
            AuthUserSession.family_id == family_id,
        ),
    ).scalar_one_or_none()
    if row is None:
        return False
    session.delete(row)
    session.flush()
    return True


def revoke_all_user_sessions(session: Session, *, user_id: str) -> list[str]:
    """Borra TODAS las sesiones del user. Devuelve los family_id borrados
    (para blacklistear cada familia en DDB)."""
    families = list(
        session.execute(
            select(AuthUserSession.family_id).where(
                AuthUserSession.user_id == user_id,
            ),
        ).scalars(),
    )
    session.execute(
        delete(AuthUserSession).where(AuthUserSession.user_id == user_id),
    )
    session.flush()
    return families


# ----- Admin actions + consent -----


def insert_admin_action(
    session: Session,
    *,
    admin_user_id: str | None,
    target_user_id: str | None,
    action: str,
    meta_data: dict[str, Any] | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> AuthUserAdminAction:
    """Inserta un row de audit admin (inmutable)."""
    row = AuthUserAdminAction(
        admin_user_id=admin_user_id,
        target_user_id=target_user_id,
        action=action,
        meta_data=meta_data,
        ip=ip,
        user_agent=user_agent,
    )
    session.add(row)
    session.flush()
    return row


def list_admin_actions(
    session: Session,
    *,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    page_size: int = 50,
    cursor: str | None = None,
) -> list[AuthUserAdminAction]:
    """Lista admin actions en un rango, created_at DESC, paginado por id."""
    stmt = select(AuthUserAdminAction)
    if from_date is not None:
        stmt = stmt.where(AuthUserAdminAction.created_at >= from_date)
    if to_date is not None:
        stmt = stmt.where(AuthUserAdminAction.created_at <= to_date)
    if cursor is not None:
        stmt = stmt.where(AuthUserAdminAction.id < cursor)
    stmt = stmt.order_by(AuthUserAdminAction.id.desc()).limit(page_size)
    return list(session.execute(stmt).scalars())


def insert_email_change_link(
    session: Session,
    *,
    user_id: str,
    token_hash: bytes,
    expires_at: datetime,
    new_email: str,
    ip: str | None = None,
    user_agent: str | None = None,
) -> AuthMagicLink:
    """Inserta un magic-link kind=email-change con `{new_email}` en metadata."""
    row = AuthMagicLink(
        user_id=user_id,
        token_hash=token_hash,
        kind=AuthLinkKind.EMAIL_CHANGE,
        expires_at=expires_at,
        ip=ip,
        user_agent=user_agent,
        meta_data={'new_email': new_email.strip().lower()},
    )
    session.add(row)
    session.flush()
    return row


def get_email_change_link(
    session: Session,
    *,
    token_hash: bytes,
) -> AuthMagicLink | None:
    """Lookup (read-only) de un magic-link email-change por token_hash."""
    return session.execute(
        select(AuthMagicLink).where(
            AuthMagicLink.token_hash == token_hash,
            AuthMagicLink.kind == AuthLinkKind.EMAIL_CHANGE,
        ),
    ).scalar_one_or_none()


def consume_email_change_link(
    session: Session,
    *,
    token_hash: bytes,
    when: datetime | None = None,
) -> AuthMagicLink | None:
    """Consume (single-use) un magic-link email-change vigente.

    Devuelve el row (con `meta_data['new_email']`) si el link existe, es
    kind=email-change, NO esta consumido y NO esta expirado; lo marca
    consumed. None en cualquier otro caso.
    """
    now = _now(when)
    row = session.execute(
        select(AuthMagicLink).where(
            AuthMagicLink.token_hash == token_hash,
            AuthMagicLink.kind == AuthLinkKind.EMAIL_CHANGE,
        ),
    ).scalar_one_or_none()
    if row is None or row.consumed_at is not None or row.expires_at <= now:
        return None
    row.consumed_at = now
    session.flush()
    return row


def insert_consent_log(
    session: Session,
    *,
    user_id: str,
    field: str,
    old_value: str | None,
    new_value: str | None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> AuthUserConsentLog:
    """Inserta un row de consent log (GDPR)."""
    row = AuthUserConsentLog(
        user_id=user_id,
        field=field,
        old_value=old_value,
        new_value=new_value,
        ip=ip,
        user_agent=user_agent,
    )
    session.add(row)
    session.flush()
    return row


def count_users(
    session: Session,
    *,
    status_filter: str | None = None,
) -> int:
    """Cuenta total de users (no borrados), opcionalmente por status."""
    stmt = (
        select(func.count())
        .select_from(AuthUser)
        .where(
            AuthUser.deleted_at.is_(None),
        )
    )
    if status_filter is not None:
        stmt = stmt.where(AuthUser.status == AuthUserStatus(status_filter))
    return int(session.scalar(stmt) or 0)


def count_remaining_recovery_codes(session: Session, *, user_id: str) -> int:
    """Cuenta los recovery codes del user que NO se consumieron."""
    stmt = (
        select(func.count())
        .select_from(AuthMfaRecoveryCode)
        .where(
            AuthMfaRecoveryCode.user_id == user_id,
            AuthMfaRecoveryCode.consumed_at.is_(None),
        )
    )
    return int(session.scalar(stmt) or 0)


def count_recovery_codes(session: Session, *, user_id: str) -> int:
    """Cuenta TODOS los recovery codes del user (consumidos + activos)."""
    stmt = (
        select(func.count())
        .select_from(AuthMfaRecoveryCode)
        .where(AuthMfaRecoveryCode.user_id == user_id)
    )
    return int(session.scalar(stmt) or 0)


def get_password_status(
    session: Session,
    *,
    user_id: str,
) -> dict[str, object | None]:
    """Estado de la password del user para el overview de seguridad.

    `auth_credentials` es 1-to-0..1 con `auth_users`: solo existe si el
    user llamo `verify.set-password`. Devuelve siempre el mismo shape:
    `{has_password: bool, required: bool, last_change_at: str | None}`
    (ISO 8601). `required` refleja si la password se exige al loguear
    (factor de la lista; default true si existe).
    """
    cred = session.get(AuthCredentials, str(user_id))
    if cred is None:
        return {
            'has_password': False,
            'required': False,
            'last_change_at': None,
        }
    return {
        'has_password': True,
        'required': bool(cred.required),
        'last_change_at': cred.last_change_at.isoformat(),
    }


def count_user_sessions(session: Session, *, user_id: str) -> int:
    """Cuenta las sesiones activas del user."""
    stmt = (
        select(func.count())
        .select_from(AuthUserSession)
        .where(AuthUserSession.user_id == user_id)
    )
    return int(session.scalar(stmt) or 0)


def list_recent_audit(
    session: Session,
    *,
    user_id: str,
    limit: int = 10,
) -> list[AuthAuditLog]:
    """Lista los ultimos `limit` eventos de auth_audit_log del user."""
    stmt = (
        select(AuthAuditLog)
        .where(AuthAuditLog.user_id == user_id)
        .order_by(AuthAuditLog.created_at.desc())
        .limit(limit)
    )
    return list(session.execute(stmt).scalars())
