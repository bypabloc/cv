"""
Subpaquete `auth`: JWT (HS256), argon2id hashing, generadores de codes
y tokens opacos.

Portador unico de `pyjwt` y `argon2-cffi` segun el contrato
`.claude/rules/lambda-shared-imports.md`. Los `core/` de los Lambdas
`auth`, `auth_email_worker` y `users` NO importan `jwt`/`argon2`/`pyotp`/
`fido2` directo — pasan SIEMPRE por `shared.auth`.

Convencion: importar SIEMPRE desde `shared.auth` (o el modulo
correspondiente si se necesita un simbolo no re-exportado).

Carga LAZY (PEP 562 `__getattr__`): cada simbolo se importa de su
submodulo SOLO cuando se accede. Sin esto, importar cualquier cosa de
`shared.auth` ejecutaba este `__init__` que hacia `from
shared.auth.webauthn import ...` eager -> arrastraba fido2/cryptography
(el import mas caro) en el cold start de TODA accion, aunque no use
WebAuthn (ej. `login.start`, `session.refresh`). Con el lazy, una accion
solo paga los submodulos que toca. Ver `.claude/rules/lambda-config.md`.
"""

from importlib import import_module
from typing import TYPE_CHECKING

# Mapa simbolo publico -> submodulo que lo define. Fuente de verdad del
# re-export lazy: cada entrada de `__all__` DEBE estar aca.
_SUBMODULE_BY_SYMBOL: dict[str, str] = {
    # admin (shared.aws para la whitelist SSM)
    'AdminAuthzError': 'admin',
    'is_admin': 'admin',
    'load_admin_emails': 'admin',
    'require_admin': 'admin',
    # codes (hashlib + secrets, barato)
    'CODE_ALPHABET': 'codes',
    'CODE_LENGTH': 'codes',
    'compare_code': 'codes',
    'generate_code': 'codes',
    'hash_code': 'codes',
    # constants (barato)
    'ACCESS_TTL': 'constants',
    'DEFAULT_AUDIENCE': 'constants',
    'DEFAULT_ISSUER': 'constants',
    'JWT_ALGORITHM': 'constants',
    'REFRESH_TTL': 'constants',
    'TEMP_TTL': 'constants',
    'TOKEN_BYTES': 'constants',
    # jwt (pyjwt)
    'JwtClaims': 'jwt',
    'JwtError': 'jwt',
    'JwtExpiredError': 'jwt',
    'JwtInvalidError': 'jwt',
    'JwtRevokedError': 'jwt',
    'issue_access_jwt': 'jwt',
    'issue_refresh_jwt': 'jwt',
    'issue_temp_jwt': 'jwt',
    'verify_jwt': 'jwt',
    # password (argon2-cffi -> cffi, pesado)
    'NeedsRehashError': 'password',
    'PasswordError': 'password',
    'hash_password': 'password',
    'verify_password': 'password',
    # recovery_codes (hashlib + secrets, barato)
    'RECOVERY_CODE_ALPHABET': 'recovery_codes',
    'RECOVERY_CODE_COUNT': 'recovery_codes',
    'RECOVERY_CODE_LENGTH': 'recovery_codes',
    'compare_recovery_code': 'recovery_codes',
    'generate_recovery_codes': 'recovery_codes',
    'hash_recovery_code': 'recovery_codes',
    # tokens (hashlib + secrets, barato)
    'compare_token': 'tokens',
    'generate_opaque_token': 'tokens',
    'hash_token': 'tokens',
    # totp (pyotp)
    'TotpError': 'totp',
    'build_otpauth_url': 'totp',
    'generate_totp_secret_b32': 'totp',
    'verify_totp_code': 'totp',
    # webauthn (fido2 -> cryptography, el mas pesado)
    'WebauthnCloneError': 'webauthn',
    'WebauthnError': 'webauthn',
    'WebauthnVerifyError': 'webauthn',
    'build_login_options': 'webauthn',
    'build_register_options': 'webauthn',
    'verify_authentication': 'webauthn',
    'verify_registration': 'webauthn',
}


def __getattr__(name: str) -> object:
    """PEP 562: importa el submodulo del simbolo on-demand y lo cachea."""
    submodule = _SUBMODULE_BY_SYMBOL.get(name)
    if submodule is None:
        msg = f"module 'shared.auth' has no attribute '{name}'"
        raise AttributeError(msg)
    value = getattr(import_module(f'shared.auth.{submodule}'), name)
    globals()[name] = value  # cache: accesos futuros sin re-import
    return value


def __dir__() -> list[str]:
    return sorted(_SUBMODULE_BY_SYMBOL)


if TYPE_CHECKING:  # los type checkers / IDE ven los simbolos reales
    from shared.auth.admin import (
        AdminAuthzError,
        is_admin,
        load_admin_emails,
        require_admin,
    )
    from shared.auth.codes import (
        CODE_ALPHABET,
        CODE_LENGTH,
        compare_code,
        generate_code,
        hash_code,
    )
    from shared.auth.constants import (
        ACCESS_TTL,
        DEFAULT_AUDIENCE,
        DEFAULT_ISSUER,
        JWT_ALGORITHM,
        REFRESH_TTL,
        TEMP_TTL,
        TOKEN_BYTES,
    )
    from shared.auth.jwt import (
        JwtClaims,
        JwtError,
        JwtExpiredError,
        JwtInvalidError,
        JwtRevokedError,
        issue_access_jwt,
        issue_refresh_jwt,
        issue_temp_jwt,
        verify_jwt,
    )
    from shared.auth.password import (
        NeedsRehashError,
        PasswordError,
        hash_password,
        verify_password,
    )
    from shared.auth.recovery_codes import (
        RECOVERY_CODE_ALPHABET,
        RECOVERY_CODE_COUNT,
        RECOVERY_CODE_LENGTH,
        compare_recovery_code,
        generate_recovery_codes,
        hash_recovery_code,
    )
    from shared.auth.tokens import (
        compare_token,
        generate_opaque_token,
        hash_token,
    )
    from shared.auth.totp import (
        TotpError,
        build_otpauth_url,
        generate_totp_secret_b32,
        verify_totp_code,
    )
    from shared.auth.webauthn import (
        WebauthnCloneError,
        WebauthnError,
        WebauthnVerifyError,
        build_login_options,
        build_register_options,
        verify_authentication,
        verify_registration,
    )

__all__ = [
    'ACCESS_TTL',
    'CODE_ALPHABET',
    'CODE_LENGTH',
    'DEFAULT_AUDIENCE',
    'DEFAULT_ISSUER',
    'JWT_ALGORITHM',
    'RECOVERY_CODE_ALPHABET',
    'RECOVERY_CODE_COUNT',
    'RECOVERY_CODE_LENGTH',
    'REFRESH_TTL',
    'TEMP_TTL',
    'TOKEN_BYTES',
    'AdminAuthzError',
    'JwtClaims',
    'JwtError',
    'JwtExpiredError',
    'JwtInvalidError',
    'JwtRevokedError',
    'NeedsRehashError',
    'PasswordError',
    'TotpError',
    'WebauthnCloneError',
    'WebauthnError',
    'WebauthnVerifyError',
    'build_login_options',
    'build_otpauth_url',
    'build_register_options',
    'compare_code',
    'compare_recovery_code',
    'compare_token',
    'generate_code',
    'generate_opaque_token',
    'generate_recovery_codes',
    'generate_totp_secret_b32',
    'hash_code',
    'hash_password',
    'hash_recovery_code',
    'hash_token',
    'is_admin',
    'issue_access_jwt',
    'issue_refresh_jwt',
    'issue_temp_jwt',
    'load_admin_emails',
    'require_admin',
    'verify_authentication',
    'verify_jwt',
    'verify_password',
    'verify_registration',
    'verify_totp_code',
]
