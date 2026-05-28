# 03. Shared subpackage `shared.auth`

> Portador unico de las dependencias de autenticacion: `pyjwt`,
> `argon2-cffi`. Expone helpers puros (sin side-effects) que los
> Lambdas `auth` y `auth_email_worker` (y mas adelante `users`)
> consumen via `from shared.auth import ...`.

## Justificacion del subpackage nuevo

Segun `.claude/rules/lambda-shared-imports.md`, cada paquete externo
nuevo debe tener UN portador shared. Hoy:

| Paquete | Portador existente | Notas |
|---------|--------------------|-------|
| pyjwt | (no existe) | nuevo |
| argon2-cffi | (no existe) | nuevo |
| pydantic | shared.core | existente |
| boto3 (ssm/ses/dynamodb) | shared.aws | existente |
| sqlalchemy | shared.db | existente |

Crear `shared.auth` mantiene el patron "un dominio, un subpackage".
Alternativa rechazada: meter pyjwt/argon2 en `shared.core` rompe la
cohesion (core es bootstrap/utilities transversales, no dominio).

## Estructura

```text
serverless/lambda/shared/auth/
├── __init__.py        # re-exports + __all__
├── pyproject.toml     # [project.dependencies] + [tool.shared].internal-deps
├── jwt.py             # issue_*, verify_*, JwtClaims (Pydantic), JwtError
├── password.py        # hash_password, verify_password, NeedsRehashError
├── codes.py           # generate_code (8 chars Crockford), hash_code, compare_code
├── tokens.py          # generate_opaque_token (32 bytes), hash_token, compare_token
└── constants.py       # JWT_ALGORITHM='HS256', CODE_ALPHABET, CODE_LENGTH=8, ...
```

## `pyproject.toml`

```toml
[project]
name = "shared-auth"
version = "0.1.0"
requires-python = ">=3.13,<3.15"
dependencies = [
    "pyjwt>=2.9,<3.0",
    "argon2-cffi>=23.1,<24.0",
]

[tool.shared]
internal-deps = ["core", "aws", "observability"]
```

`internal-deps`:
- `core` -> `BaseModel` / `Field` / `ApplicationError` / `new_uuidv7`.
- `aws` -> `get_secret_by_name` (lee `/portfolio/${stage}/jwt-secret`).
- `observability` -> `logger`, `metrics`.

NOTA: el cierre transitivo arrastrara `pydantic` (de core), `boto3` (de aws),
`aws-lambda-powertools` (de observability). Los Lambdas que ya tienen
estos en su cierre NO los duplican (la regla D-3 lo enforza con
`serverless lint-deps`).

## `__init__.py` (re-exports)

```python
"""shared.auth — JWT, password hashing y generadores de codes/tokens."""

from .codes import (
    CODE_ALPHABET,
    CODE_LENGTH,
    compare_code,
    generate_code,
    hash_code,
)
from .jwt import (
    JWT_ALGORITHM,
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
from .password import (
    NeedsRehashError,
    PasswordError,
    hash_password,
    verify_password,
)
from .tokens import (
    compare_token,
    generate_opaque_token,
    hash_token,
)

__all__ = [
    'CODE_ALPHABET',
    'CODE_LENGTH',
    'JWT_ALGORITHM',
    'JwtClaims',
    'JwtError',
    'JwtExpiredError',
    'JwtInvalidError',
    'JwtRevokedError',
    'NeedsRehashError',
    'PasswordError',
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
```

## `jwt.py` — API

```python
JWT_ALGORITHM = 'HS256'

# Lifetimes (en segundos)
TEMP_TTL = 300       # 5 min
ACCESS_TTL = 900     # 15 min
REFRESH_TTL = 30 * 24 * 3600  # 30 dias


class JwtClaims(BaseModel):
    """Claims canonicos. Subset de RFC 7519 + custom."""
    sub: UUID                          # subject = user_id
    jti: UUID                          # JWT ID (uuidv7)
    typ: Literal['temp', 'access', 'refresh']
    iat: int                           # issued at (unix)
    exp: int                           # expires at (unix)
    iss: str = 'portfolio-auth'
    aud: str = 'portfolio'
    # custom
    flow: str | None = None            # solo en typ=temp
    step: int | None = None            # solo en typ=temp
    family_id: UUID | None = None      # solo en typ=refresh
    email: str | None = None           # incluido en access para evitar lookup
    niche: str | None = None           # opcional para tracking


def issue_temp_jwt(
    *, user_id: UUID, flow: str, step: int, secret: str,
    ttl: int = TEMP_TTL, niche: str | None = None,
) -> tuple[str, JwtClaims]:
    """Emite un JWT temporal. Retorna (token_string, claims)."""

def issue_access_jwt(
    *, user_id: UUID, email: str, secret: str,
    ttl: int = ACCESS_TTL, niche: str | None = None,
) -> tuple[str, JwtClaims]:
    """Emite un JWT access. Retorna (token_string, claims)."""

def issue_refresh_jwt(
    *, user_id: UUID, family_id: UUID, secret: str,
    ttl: int = REFRESH_TTL,
) -> tuple[str, JwtClaims]:
    """Emite un JWT refresh. family_id agrupa todos los refresh
    rotados del mismo session para detectar token reuse."""

def verify_jwt(
    token: str, *, secret: str, expected_typ: str | None = None,
) -> JwtClaims:
    """Valida signature + exp + aud. NO verifica blacklist (eso lo
    hace el Lambda contra DynamoDB).

    Raises:
      JwtExpiredError: si exp < now
      JwtInvalidError: si signature mismatch, aud mismatch, typ mismatch
    """


class JwtError(ApplicationError): ...
class JwtExpiredError(JwtError): ...
class JwtInvalidError(JwtError): ...
class JwtRevokedError(JwtError): ...  # se levanta desde el Lambda tras DDB lookup
```

## `password.py` — API

```python
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHash

_hasher = PasswordHasher()  # defaults: time_cost=3, memory_cost=64MiB, parallelism=4

class PasswordError(ApplicationError): ...
class NeedsRehashError(PasswordError): ...  # password OK pero parametros cambiaron


def hash_password(password: str) -> str:
    """Retorna el hash argon2id en formato $argon2id$...$ ready para guardar."""

def verify_password(*, password: str, hashed: str) -> bool:
    """True si match. False si mismatch. Si hash usa params viejos,
    levanta NeedsRehashError para forzar rehash en background."""
```

## `codes.py` — API

```python
CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'  # 30 chars, Crockford-like
CODE_LENGTH = 8

def generate_code() -> str:
    """8 chars random del alfabeto. CSPRNG (secrets.choice)."""

def hash_code(code: str) -> bytes:
    """SHA-256 (32 bytes). Guardado en auth_email_codes.code_hash (BYTEA)."""

def compare_code(*, code: str, stored_hash: bytes) -> bool:
    """secrets.compare_digest(hash(code), stored_hash). Resistente a timing."""
```

## `tokens.py` — API

```python
def generate_opaque_token(num_bytes: int = 32) -> str:
    """secrets.token_urlsafe(num_bytes). 32 bytes -> ~43 chars b64url."""

def hash_token(token: str) -> bytes:
    """SHA-256 del token. Guardado en auth_magic_links.token_hash."""

def compare_token(*, token: str, stored_hash: bytes) -> bool:
    """secrets.compare_digest(hash(token), stored_hash)."""
```

## Tests unit (`shared/tests/unit/shared/auth/`)

| Archivo | Que testea |
|---------|-----------|
| `test_jwt_issue_and_verify.py` | Round-trip: issue_temp -> verify -> claims correctas |
| `test_jwt_expired.py` | Token con `exp < now` levanta `JwtExpiredError` |
| `test_jwt_wrong_typ.py` | `expected_typ='access'` sobre un temp levanta `JwtInvalidError` |
| `test_jwt_signature_mismatch.py` | Cambiar 1 byte de la signature levanta `JwtInvalidError` |
| `test_jwt_aud_mismatch.py` | Token con `aud='other'` levanta `JwtInvalidError` |
| `test_jwt_refresh_family_id.py` | refresh JWT preserva `family_id` |
| `test_password_hash_verify.py` | hash + verify -> True |
| `test_password_verify_wrong.py` | verify con password incorrecta -> False |
| `test_password_needs_rehash.py` | hash con params viejos -> verify levanta `NeedsRehashError` |
| `test_codes_generate_alphabet.py` | 1000 codes -> todos en `CODE_ALPHABET`, todos length 8 |
| `test_codes_generate_uniqueness.py` | 1000 codes -> >995 unicos (1-in-30^8 collision) |
| `test_codes_hash_compare_ok.py` | hash + compare correcta -> True |
| `test_codes_hash_compare_wrong.py` | compare con code incorrecto -> False |
| `test_codes_compare_timing_safe.py` | (smoke) compara correcto e incorrecto en tiempo similar |
| `test_tokens_generate.py` | length >= 32 chars, url-safe (sin `+/=`) |
| `test_tokens_hash_compare.py` | round-trip |
| `test_reexport_smoke.py` | from shared.auth import * y verifica `__all__` completo |

Cada archivo = 1 funcion `test_<nombre>` con docstring Given/When/Then.

## Anti-patrones aplicables a este modulo

| Anti-patron | Correccion |
|-------------|------------|
| `import jwt` en el `core/` de un Lambda | `from shared.auth import issue_*, verify_jwt` |
| `import argon2` en el `core/` de un Lambda | `from shared.auth import hash_password, verify_password` |
| Guardar el code en plain text en Neon | Solo `code_hash` (BYTEA, SHA-256) |
| Generar code con `random.choice` | `secrets.choice` obligatorio |
| Comparar codes con `==` | `compare_code(...)` (timing-safe) |
| Hardcodear el JWT secret en el codigo | Leer de SSM `get_secret_by_name('jwt-secret', ...)` en cold start |
| Reusar el mismo `family_id` entre logout y nuevo login | Cada login emite un `family_id` nuevo (`uuidv7()`) |
