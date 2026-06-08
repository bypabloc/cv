"""MFA method service: orquesta `auth_mfa_methods` (TOTP + email_code).

Envuelve el repository `shared.db.repositories.auth_mfa` con la logica de
sesion + el side-effect de AC-27 (revocar las sesiones del user al
confirmar su PRIMER metodo MFA — transicion total_mfa 0 -> 1).

Devuelve primitivos (bool / list[dict] / bytes), NUNCA objetos ORM
detached, para que los controllers no toquen la sesion.
"""

from __future__ import annotations

from uuid import UUID

from shared.db.models.auth.enums import AuthMfaKind
from shared.db.repositories.auth import get_password_required
from shared.db.repositories.auth_mfa import (
    confirm_mfa,
    count_active_mfa,
    count_active_strong_mfa,
    delete_mfa,
    disable_mfa,
    enable_mfa,
    get_all_mfa_methods,
    get_mfa_method,
    list_mfa_methods,
    list_required_methods,
    mark_method_used,
    set_preferred,
    set_required,
    upsert_totp_method,
)
from shared.db.session import db_session

# Config minima de render por metodo (lo que el front necesita para montar el
# input del checklist). Sin secretos: solo el hint de widget + la action a la
# que el front debe pegar para verificar / pre-disparar el metodo.
_METHOD_CONFIG: dict[str, dict[str, object | None]] = {
    'password': {
        'input': 'password',
        'sent': None,
        'dispatch_action': 'login.verify-password',
    },
    'passwordless': {
        'input': 'email',
        'sent': None,
        'dispatch_action': 'login.send-email-code',
    },
    'totp': {
        'input': 'code6',
        'sent': None,
        'dispatch_action': 'login.verify-totp',
    },
    'email_code': {
        'input': 'code8',
        'sent': False,
        'dispatch_action': 'login.send-email-code',
    },
    'webauthn': {
        'input': 'webauthn',
        'sent': None,
        'dispatch_action': 'webauthn.login-options',
    },
}
# Orden fijo de presentacion en el checklist (solo UX; el backend usa
# conjuntos, el orden no afecta la igualdad de los `satisfied`).
_METHOD_ORDER = ('password', 'passwordless', 'totp', 'email_code', 'webauthn')


def compose_required(
    *, password_required: bool, mfa_required: list[str],
) -> list[str]:
    """Compone la lista de factores que el login EXIGE, en orden fijo.

    Funcion pura (sin DB) para poder testear el invariante:
    - `password` al frente si esta required.
    - los MFA required (`totp`/`email_code`/`webauthn`) a continuacion.
    - `passwordless` como FALLBACK SOLO si no hay ningun otro factor: es el
      metodo por defecto (un user recien registrado entra passwordless) y
      garantiza "siempre >=1 required".

    Returns la lista deduplicada y ordenada por `_METHOD_ORDER`.
    """
    required: list[str] = []
    if password_required:
        required.append('password')
    required.extend(mfa_required)
    if not required:
        required = ['passwordless']
    return [m for m in _METHOD_ORDER if m in required]

from .session_service import SessionService


class MfaMethodService:
    """CRUD de `auth_mfa_methods` + revocacion de sesiones en el primer MFA."""

    def __init__(self, app_config: object) -> None:
        self.app_config = app_config

    def list_active(self, *, user_id: UUID | str) -> list[dict]:
        """Metodos activos del user como dicts serializables."""
        with db_session() as session:
            methods = list_mfa_methods(session, user_id=str(user_id))
            return [
                {
                    'kind': method.kind.value,
                    'preferred': method.preferred,
                    'required': method.required,
                    'confirmed': method.confirmed_at is not None,
                }
                for method in methods
            ]

    def list_all(self, *, user_id: UUID | str) -> list[dict]:
        """TODOS los metodos del user (incl. desactivados) para el overview."""
        with db_session() as session:
            return [
                {
                    'kind': method.kind.value,
                    'preferred': method.preferred,
                    'required': method.required,
                    'confirmed': method.confirmed_at is not None,
                    'enabled': method.disabled_at is None,
                    'created_at': method.created_at.isoformat(),
                    'last_used_at': (
                        method.last_used_at.isoformat()
                        if method.last_used_at is not None
                        else None
                    ),
                }
                for method in get_all_mfa_methods(session, user_id=str(user_id))
            ]

    def enable(self, *, user_id: UUID | str, kind: AuthMfaKind) -> bool:
        """Re-activa el metodo (toggle-on). False si no existe (404)."""
        with db_session() as session:
            return enable_mfa(session, user_id=str(user_id), kind=kind)

    def set_required(
        self, *, user_id: UUID | str, kind: AuthMfaKind, required: bool,
    ) -> bool:
        """Marca/desmarca el metodo como requerido al loguear. False si no existe/desactivado."""
        with db_session() as session:
            return set_required(
                session, user_id=str(user_id), kind=kind, required=required,
            )

    def required_methods(self, *, user_id: UUID | str) -> list[str]:
        """Factores que el login EXIGE para este user (orden fijo).

        Modelo de lista (plan login-mfa-list-redesign): todo factor es un
        item de la lista. Composicion:

        - `password` si existe + `auth_credentials.required` (factor base
          de la lista, ya no un gate previo).
        - `totp` / `email_code` / `webauthn` con `required=true` y activos
          (lo que ya devolvia `list_required_methods`).
        - `passwordless` (email: code O magic-link) como FALLBACK: se exige
          SOLO cuando el user no tiene ningun otro factor required. Es el
          metodo por defecto (un user recien registrado entra passwordless);
          garantiza el invariante "siempre >=1 required". El guard de
          settings impide desmarcar el ultimo required, asi que un user
          nunca queda con la lista vacia.

        El orden es estable (`_METHOD_ORDER`) por UX; el motor multi-factor
        (`decide_mfa_step`) usa conjuntos, no le afecta.
        """
        with db_session() as session:
            password_required = get_password_required(
                session, user_id=str(user_id),
            )
            mfa_required = list_required_methods(
                session, user_id=str(user_id),
            )
        return compose_required(
            password_required=password_required,
            mfa_required=mfa_required,
        )

    def required_methods_config(
        self, *, user_id: UUID | str,
    ) -> list[dict[str, object | None]]:
        """`required_methods` enriquecido con la config de render por metodo.

        Lo consume `login.check-email` para devolver `methods_required`: el
        front monta un input por cada entrada (en cualquier orden) con el
        `input` (hint de widget) + `dispatch_action`. Sin secretos.
        """
        return [
            {'type': m, **_METHOD_CONFIG[m]}
            for m in self.required_methods(user_id=user_id)
        ]

    def confirmed_kinds(self, *, user_id: UUID | str) -> list[str]:
        """Kinds de los metodos confirmados y activos del user."""
        with db_session() as session:
            return [
                method.kind.value
                for method in list_mfa_methods(session, user_id=str(user_id))
                if method.confirmed_at is not None
            ]

    def upsert_pending_totp(
        self,
        *,
        user_id: UUID | str,
        ciphertext: bytes,
    ) -> None:
        """Crea/reusa el row TOTP pendiente (confirmed_at=NULL)."""
        with db_session() as session:
            upsert_totp_method(
                session,
                user_id=str(user_id),
                ciphertext=ciphertext,
            )

    def get_totp_ciphertext(
        self,
        *,
        user_id: UUID | str,
        require_confirmed: bool,
    ) -> bytes | None:
        """Ciphertext del secret TOTP del user, o None.

        `require_confirmed=True` exige el metodo confirmado y no
        deshabilitado (login); `False` acepta el pendiente (confirm-totp).
        """
        with db_session() as session:
            method = get_mfa_method(
                session,
                user_id=str(user_id),
                kind=AuthMfaKind.TOTP,
            )
            if method is None or method.totp_secret_ciphertext is None:
                return None
            if require_confirmed and (
                method.confirmed_at is None or method.disabled_at is not None
            ):
                return None
            return bytes(method.totp_secret_ciphertext)

    def confirm(self, *, user_id: UUID | str, kind: AuthMfaKind) -> bool:
        """Confirma el metodo. Si es el primer MFA FUERTE, revoca sesiones.

        El revoke se mide con `count_active_strong_mfa` (excluye email_code):
        el email_code del alta NO cuenta como "primer MFA", asi que confirmar
        el primer TOTP SI dispara la re-autenticacion (transicion 0->1 fuerte).
        El `preferred` del primer metodo confirmado (UX) sigue contando TODOS
        los confirmados, incluido email_code.
        """
        revoke = False
        with db_session() as session:
            before = count_active_strong_mfa(session, user_id=str(user_id))
            method = confirm_mfa(session, user_id=str(user_id), kind=kind)
            if method is None:
                return False
            confirmed = [
                m
                for m in list_mfa_methods(session, user_id=str(user_id))
                if m.confirmed_at is not None
            ]
            if len(confirmed) == 1:
                method.preferred = True
                session.flush()
            after = count_active_strong_mfa(session, user_id=str(user_id))
            revoke = before == 0 and after == 1
        if revoke:
            SessionService(self.app_config).revoke_all_for_user(
                user_id=user_id,
            )
        return True

    def ensure_email_code(self, *, user_id: UUID | str) -> bool:
        """Garantiza un email_code CONFIRMADO y activo, idempotente y SIN revoke.

        El email se verifica en el alta, asi que el code-por-email es un
        factor disponible desde el registro. Este metodo crea/reactiva el row
        `email_code` confirmado (required=false) si falta:

        - no existe -> INSERT confirmado.
        - existe pero no confirmado o deshabilitado -> `confirm_mfa` (re-confirma,
          limpia disabled_at).
        - existe confirmado y activo -> no-op.

        NUNCA dispara `SessionService.revoke_all_for_user`: el email_code del
        alta NO es el "primer MFA fuerte" (esa transicion la mide
        `count_active_strong_mfa` en `confirm`/webauthn). Idempotente: se invoca
        en el alta (verify-code/magic-link) y como backfill on-read del overview.

        Returns:
            True si creo o reactivo el metodo; False si ya estaba confirmado.
        """
        with db_session() as session:
            existing = get_mfa_method(
                session,
                user_id=str(user_id),
                kind=AuthMfaKind.EMAIL_CODE,
            )
            if (
                existing is not None
                and existing.confirmed_at is not None
                and existing.disabled_at is None
            ):
                return False
            if existing is None:
                from datetime import UTC, datetime

                from shared.db.models.auth.mfa_method import AuthMfaMethod

                session.add(
                    AuthMfaMethod(
                        user_id=str(user_id),
                        kind=AuthMfaKind.EMAIL_CODE,
                        confirmed_at=datetime.now(tz=UTC),
                    ),
                )
            else:
                confirm_mfa(
                    session,
                    user_id=str(user_id),
                    kind=AuthMfaKind.EMAIL_CODE,
                )
            session.flush()
            return True

    def setup_email_code(self, *, user_id: UUID | str) -> bool:
        """Activa email_code como metodo MFA (confirmado de inmediato).

        Delega en `ensure_email_code` (idempotente, sin revoke): con email_code
        ya creado en el alta, `mfa.setup-email-code` es un no-op seguro. El
        controller responde 204 incondicional.
        """
        self.ensure_email_code(user_id=user_id)
        return True

    def set_preferred(self, *, user_id: UUID | str, kind: AuthMfaKind) -> bool:
        """Marca `kind` como preferido. False si el user no tiene ese metodo."""
        with db_session() as session:
            method = get_mfa_method(
                session,
                user_id=str(user_id),
                kind=kind,
            )
            if method is None or method.disabled_at is not None:
                return False
            set_preferred(session, user_id=str(user_id), kind=kind)
        return True

    def disable(self, *, user_id: UUID | str, kind: AuthMfaKind) -> bool:
        """Deshabilita el metodo. False si no existe (controller valida count)."""
        with db_session() as session:
            return disable_mfa(session, user_id=str(user_id), kind=kind)

    def delete(self, *, user_id: UUID | str, kind: AuthMfaKind) -> bool:
        """Borra (hard-delete) el metodo. False si no existe.

        El metodo desaparece de la tabla -> vuelve a `configured:false` en el
        overview y un `setup-totp` posterior empieza de cero. El controller
        valida el guard MUST_KEEP_ONE (solo para metodos confirmados).
        """
        with db_session() as session:
            return delete_mfa(session, user_id=str(user_id), kind=kind)

    def count_active(self, *, user_id: UUID | str) -> int:
        """Cuenta transversal de metodos MFA activos (MUST_KEEP_ONE)."""
        with db_session() as session:
            return count_active_mfa(session, user_id=str(user_id))

    def has_active_method(
        self,
        *,
        user_id: UUID | str,
        kind: AuthMfaKind,
    ) -> bool:
        """True si el user tiene el metodo `kind` activo (no deshabilitado)."""
        with db_session() as session:
            method = get_mfa_method(
                session,
                user_id=str(user_id),
                kind=kind,
            )
            return method is not None and method.disabled_at is None

    def is_confirmed(
        self,
        *,
        user_id: UUID | str,
        kind: AuthMfaKind,
    ) -> bool:
        """True si el metodo `kind` del user esta confirmado y activo.

        Un metodo no confirmado (`confirmed_at IS NULL`, ej. un setup-totp
        abandonado) NO es una via de entrada real: no cuenta para el guard
        MUST_KEEP_ONE y por eso siempre se puede deshabilitar (anti-lockout).
        """
        with db_session() as session:
            method = get_mfa_method(
                session,
                user_id=str(user_id),
                kind=kind,
            )
            return (
                method is not None
                and method.disabled_at is None
                and method.confirmed_at is not None
            )

    def mark_used(self, *, user_id: UUID | str, kind: AuthMfaKind) -> None:
        """Setea last_used_at del metodo (login con TOTP exitoso)."""
        with db_session() as session:
            mark_method_used(session, user_id=str(user_id), kind=kind)
