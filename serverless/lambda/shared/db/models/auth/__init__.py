"""Subpaquete `auth/`: schema relacional del dominio auth (11 tablas)."""

# Cross-domain FK target: `auth_users.profile_id -> cv_profiles.id`. La
# carga per-dominio debe registrar `cv_profiles` en el MetaData o la FK no
# resuelve en INSERT/UPDATE de `auth_users` (NoReferencedTableError -> 500
# en register/login/users). Ver `.claude/rules/lambda-config.md`.
import shared.db.models.cv  # noqa: F401

from .admin_action import AuthUserAdminAction
from .audit_log import AuthAuditLog
from .consent_log import AuthUserConsentLog
from .credentials import AuthCredentials
from .email_code import AuthEmailCode
from .enums import AuthCodeKind, AuthLinkKind, AuthMfaKind, AuthUserStatus
from .magic_link import AuthMagicLink
from .mfa_method import AuthMfaMethod
from .recovery_code import AuthMfaRecoveryCode
from .user import AuthUser
from .user_session import AuthUserSession
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
    'AuthUserAdminAction',
    'AuthUserConsentLog',
    'AuthUserSession',
    'AuthUserStatus',
    'AuthWebauthnCredential',
]
