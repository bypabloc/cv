"""Subpaquete `auth/`: schema relacional del dominio auth (8 tablas)."""

from .audit_log import AuthAuditLog
from .credentials import AuthCredentials
from .email_code import AuthEmailCode
from .enums import AuthCodeKind, AuthLinkKind, AuthMfaKind, AuthUserStatus
from .magic_link import AuthMagicLink
from .mfa_method import AuthMfaMethod
from .recovery_code import AuthMfaRecoveryCode
from .user import AuthUser
from .webauthn_credential import AuthWebauthnCredential

__all__ = [
    'AuthAuditLog',
    'AuthCodeKind',
    'AuthCredentials',
    'AuthEmailCode',
    'AuthLinkKind',
    'AuthMagicLink',
    'AuthMfaKind',
    'AuthMfaMethod',
    'AuthMfaRecoveryCode',
    'AuthUser',
    'AuthUserStatus',
    'AuthWebauthnCredential',
]
