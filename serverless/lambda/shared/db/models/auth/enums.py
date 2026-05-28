"""Enums Python del dominio auth.

Mapean 1-a-1 con los tipos PostgreSQL declarados en la migration
00000002:
- `auth_user_status`     -> AuthUserStatus
- `auth_code_kind`       -> AuthCodeKind
- `auth_link_kind`       -> AuthLinkKind
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
    PASSWORD_RESET = 'password_reset'


class AuthLinkKind(StrEnum):
    """Kind del `auth_magic_links.kind` (tipo de flujo del magic-link)."""

    REGISTER = 'register'
    LOGIN = 'login'
    PASSWORD_RESET = 'password_reset'
