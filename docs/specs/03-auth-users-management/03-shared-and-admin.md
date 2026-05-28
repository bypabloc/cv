# 03. Shared.auth extension + admin whitelist

## Que se agrega al subpackage `shared.auth`

```text
serverless/lambda/shared/auth/
├── ... (archivos del plan 01 y 02)
└── admin.py              # NUEVO — load_admin_emails + is_admin + require_admin
```

NO se agregan deps externas en este plan. `admin.py` usa solo
`shared.aws.get_secret_by_name` (existente).

## `admin.py`

```python
"""shared.auth.admin — admin whitelist via SSM.

SSM path: /portfolio/${stage}/admin-emails (SecureString + KMS).
Valor: 'pacg1991@gmail.com,otro@admin.com' (lista coma-separada).

El handler `require_admin` se cachea con TTL 5 min para evitar
hit a SSM en cada request.
"""

from functools import lru_cache
from time import time

from shared.aws import get_secret_by_name
from shared.core import ApplicationError


class AdminAuthzError(ApplicationError): ...


_CACHE: dict = {'emails': frozenset(), 'expires_at': 0.0}


def load_admin_emails(*, ssm_path: str | None = None, ttl: int = 300) -> frozenset[str]:
    """Carga la lista de admin emails desde SSM con cache TTL."""
    now = time()
    if _CACHE['expires_at'] > now and _CACHE['emails']:
        return _CACHE['emails']

    raw = get_secret_by_name('admin-emails', local_env='ADMIN_EMAILS')
    if not raw:
        emails = frozenset()
    else:
        emails = frozenset(
            email.strip().lower()
            for email in raw.split(',')
            if email.strip()
        )

    _CACHE['emails'] = emails
    _CACHE['expires_at'] = now + ttl
    return emails


def is_admin(email: str, *, ttl: int = 300) -> bool:
    """True si email esta en la whitelist SSM."""
    return email.lower().strip() in load_admin_emails(ttl=ttl)


def require_admin(email: str) -> None:
    """Levanta AdminAuthzError si email no es admin."""
    if not is_admin(email):
        # Mensaje generico para evitar enumeration
        raise AdminAuthzError('NOT_FOUND', code=4040)
```

NOTA: la excepcion tiene mensaje generico (`NOT_FOUND`) en vez de
`FORBIDDEN` — esto es deliberado segun AC-11 y la regla critica del
plan ("NO-admin recibe 404 NOT_FOUND").

## Update `__init__.py` de `shared.auth`

```python
from .admin import (
    AdminAuthzError,
    is_admin,
    load_admin_emails,
    require_admin,
)

__all__ = [
    # ... existentes de plan 01 + 02
    'AdminAuthzError',
    'is_admin',
    'load_admin_emails',
    'require_admin',
]
```

## Tests unit

`shared/tests/unit/shared/auth/test_admin_*.py`:

| Archivo | Escenario |
|---------|-----------|
| `test_admin_load_emails_parses_comma_separated.py` | 'a@x,b@y' -> {a@x, b@y} |
| `test_admin_load_emails_lowercases.py` | 'A@X.com' -> {a@x.com} |
| `test_admin_load_emails_strips_whitespace.py` | ' a@x , b@y ' -> {a@x, b@y} |
| `test_admin_load_emails_empty_returns_frozenset.py` | '' -> frozenset() |
| `test_admin_load_emails_caches.py` | 2nd call dentro de TTL no llama SSM |
| `test_admin_load_emails_refreshes_after_ttl.py` | tras TTL=0 vuelve a llamar |
| `test_admin_is_admin_true.py` | email en lista -> True |
| `test_admin_is_admin_false.py` | email no en lista -> False |
| `test_admin_is_admin_case_insensitive.py` | 'X@Y.com' matchea 'x@y.com' |
| `test_admin_require_admin_ok.py` | no levanta para admin |
| `test_admin_require_admin_raises_with_404.py` | levanta AdminAuthzError code=4040 |

## SSM — `/portfolio/${stage}/admin-emails`

`serverless/lambda/resources/secrets/admin-emails.yaml`:

```yaml
short_name: admin-emails
description: Comma-separated list of admin user emails (whitelist)
type: SecureString
kms_key: alias/portfolio-lambdas
ssm_path: /portfolio/${stage}/admin-emails
source_env_var: ADMIN_EMAILS                # docker/env/server/.{stage}
local_env_var: ADMIN_EMAILS
rotation_interval_days: 365                  # raro cambiar
consumers:
  - lambda: users
```

**Valor inicial**: `pacg1991@gmail.com` (email del owner, segun memoria
del proyecto). Configurar en `docker/env/server/.{stage}`:

```text
ADMIN_EMAILS=pacg1991@gmail.com
```

Sincronizar:

```bash
serverless sync-secrets --stage=dev --aws-profile=tfs-dev
serverless sync-secrets --stage=stage --aws-profile=tfs-dev
serverless sync-secrets --stage=prod --aws-profile=tfs-dev
```

## Helper en el Lambda `users`

`services/users/core/services/admin_service.py`:

```python
from shared.auth import require_admin
from shared.lambda_kit import BaseController

from ..settings.config import app_config
from .audit_admin_service import AuditAdminService


def require_admin_user(user, *, ip, audit_action='admin.access') -> None:
    """Valida que `user.email` este en SSM admin-emails. Si NO,
    levanta 404 (oculta la existencia del endpoint).

    Tambien escribe un audit log antes de devolver, para registrar
    incluso los attempts fallidos (defensa contra brute force admin).
    """
    audit = AuditAdminService(app_config)
    try:
        require_admin(user.email)
    except Exception:
        audit.log_attempt(admin_user_id=user.id, action=audit_action,
                          success=False, ip=ip)
        raise
    audit.log_attempt(admin_user_id=user.id, action=audit_action,
                      success=True, ip=ip)
```

Cada controller admin lo llama al inicio del `validate()`.

## Update al catalogo de portadores

NO se agregan paquetes externos. `shared.auth.admin` solo usa
`shared.aws.get_secret_by_name` (catalogo ya tiene boto3 via
shared.aws). Update minimo al catalogo: registrar
`load_admin_emails`, `is_admin`, `require_admin` en la tabla de
re-exports de `shared.auth` si decidimos exponerlos.
