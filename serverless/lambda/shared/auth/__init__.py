"""
Subpaquete `auth`: JWT (HS256), argon2id hashing, generadores de codes
y tokens opacos.

Portador unico de `pyjwt` y `argon2-cffi` segun el contrato
`.claude/rules/lambda-shared-imports.md`. Los `core/` de los Lambdas
`auth` y `auth_email_worker` (y mas adelante `users`) NO importan
`jwt`/`argon2` directo — pasan SIEMPRE por `shared.auth`.

Convencion: importar SIEMPRE desde `shared.auth` (o el modulo
correspondiente si se necesita un simbolo no re-exportado).
"""

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
    'issue_access_jwt',
    'issue_refresh_jwt',
    'issue_temp_jwt',
    'verify_authentication',
    'verify_jwt',
    'verify_password',
    'verify_registration',
    'verify_totp_code',
]
