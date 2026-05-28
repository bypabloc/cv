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
from shared.auth.tokens import (
    compare_token,
    generate_opaque_token,
    hash_token,
)

__all__ = [
    'ACCESS_TTL',
    'CODE_ALPHABET',
    'CODE_LENGTH',
    'DEFAULT_AUDIENCE',
    'DEFAULT_ISSUER',
    'JWT_ALGORITHM',
    'JwtClaims',
    'JwtError',
    'JwtExpiredError',
    'JwtInvalidError',
    'JwtRevokedError',
    'NeedsRehashError',
    'PasswordError',
    'REFRESH_TTL',
    'TEMP_TTL',
    'TOKEN_BYTES',
    'compare_code',
    'compare_token',
    'generate_code',
    'generate_opaque_token',
    'hash_code',
    'hash_password',
    'hash_token',
    'issue_access_jwt',
    'issue_refresh_jwt',
    'issue_temp_jwt',
    'verify_jwt',
    'verify_password',
]
