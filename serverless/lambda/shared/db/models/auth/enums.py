"""Enums Python del dominio auth.

Mapean 1-a-1 con los tipos PostgreSQL declarados en las migrations:
- `auth_user_status`     -> AuthUserStatus   (00000002)
- `auth_code_kind`       -> AuthCodeKind      (00000002)
- `auth_link_kind`       -> AuthLinkKind      (00000002)
- `auth_mfa_kind`        -> AuthMfaKind       (00000003)
"""

from enum import StrEnum


class AuthUserStatus(StrEnum):
    """Estados del usuario en `auth_users.status`.

    - `pending`: registro iniciado pero magic-link / code no verificado.
    - `active`: validado y operativo.
    - `disabled`: deshabilitado por admin (plan 3).
    - `locked`: bloqueo automatico tras 5+ fallos en 5 min.
    - `deleted`: soft-delete (futuro plan 3).
    """

    PENDING = 'pending'
    ACTIVE = 'active'
    DISABLED = 'disabled'
    LOCKED = 'locked'
    DELETED = 'deleted'


class AuthCodeKind(StrEnum):
    """Kind del `auth_email_codes.kind` (tipo de flujo del code).

    Identico a `AuthLinkKind` por convencion; viven separados porque sus
    semánticas pueden divergir (ej. plan 02 agrega `mfa_setup`).
    """

    REGISTER = 'register'
    LOGIN = 'login'
    PASSWORD_RESET = 'password_reset'  # noqa: S105 (enum value, no secreto)


class AuthLinkKind(StrEnum):
    """Kind del `auth_magic_links.kind` (tipo de flujo del magic-link).

    `email-change` (plan 03) reusa la tabla `auth_magic_links` para el
    flujo de cambio de email: el user pide el cambio, recibe un magic-link
    al email NUEVO y al confirmarlo se actualiza `auth_users.email`. El
    nuevo email viaja en `auth_magic_links.meta_data` (`{new_email}`).
    """

    REGISTER = 'register'
    LOGIN = 'login'
    PASSWORD_RESET = 'password_reset'  # noqa: S105 (enum value, no secreto)
    EMAIL_CHANGE = 'email-change'


class AuthMfaKind(StrEnum):
    """Kind del `auth_mfa_methods.kind` (tipo de metodo MFA).

    - `totp`: RFC 6238 (Google Authenticator / Authy / 1Password).
    - `email_code`: el code de 8 chars al email, promovido a 2do factor
      cuando el user ya se autentico con password/passkey.

    WebAuthn / Passkeys NO es un `AuthMfaKind`: vive en su propia tabla
    `auth_webauthn_credentials`, no en `auth_mfa_methods`.
    """

    TOTP = 'totp'
    EMAIL_CODE = 'email_code'
