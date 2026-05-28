# 04. Infraestructura — Lambda `users` + SSM admin-emails + email-worker plantillas

## Resumen

| Recurso | Archivo | Que es |
|---------|---------|--------|
| SSM `/portfolio/${stage}/admin-emails` | `resources/secrets/admin-emails.yaml` | Whitelist de emails admin |
| Lambda `users` manifest | `services/users/manifest.yaml` | Nuevo Lambda HTTP `POST /users` |
| Email worker — 3 plantillas nuevas | `services/auth_email_worker/core/templates/{es,en}/{email-changed,account-disabled,account-deleted}.{txt,html}` | + 3 nuevos `kinds` en el worker |

NO se crean tablas DDB nuevas (sessions tracking vive en Neon). NO
se crean SQS nuevas. NO se modifica API Gateway directamente — el
provisioner del repo agrega la ruta `/users` automaticamente desde el
manifest del Lambda.

## 1. Lambda `users` (manifest)

`serverless/lambda/services/users/manifest.yaml`:

```yaml
name: users
trigger:
  type: http
  method: POST
  path: /users
runtime: python3.13
handler: core.handler.lambda_handler
memory: 384
timeout: 15
snap_start: true
uses:
  queues:
    - name: portfolio-auth-email-${stage}     # publica emails de change-email, account-disabled, etc.
      access: producer
  tables:
    cache: read-write
    rate-limit-rules: read-write
    rate-limit-buckets: read-write
    jwt-blacklist: read-write                  # para revoke-session / force-logout
  secrets:
    - neon-url
    - jwt-secret
    - admin-emails                              # NUEVO
    - ses-from-address
  sends-email: false
env:
  default:
    LOG_LEVEL: INFO
    POWERTOOLS_SERVICE_NAME: users
    POWERTOOLS_METRICS_NAMESPACE: Portfolio/Users
    JWT_ISSUER: portfolio-auth
    JWT_AUDIENCE: portfolio
  dev:
    CORS_ALLOWED_ORIGINS: 'https://portfolio.dev.the-full-stack.com,https://hub.portfolio.dev.the-full-stack.com,https://fintech.portfolio.dev.the-full-stack.com,https://architect.portfolio.dev.the-full-stack.com,https://leader.portfolio.dev.the-full-stack.com,https://vibe.portfolio.dev.the-full-stack.com,http://localhost:9970'
  stage:
    CORS_ALLOWED_ORIGINS: 'https://portfolio.stage.the-full-stack.com,https://hub.portfolio.stage.the-full-stack.com,https://fintech.portfolio.stage.the-full-stack.com,https://architect.portfolio.stage.the-full-stack.com,https://leader.portfolio.stage.the-full-stack.com,https://vibe.portfolio.stage.the-full-stack.com'
  prod:
    LOG_LEVEL: WARNING
    CORS_ALLOWED_ORIGINS: 'https://the-full-stack.com,https://www.the-full-stack.com,https://portfolio.the-full-stack.com,https://hub.portfolio.the-full-stack.com,https://fintech.portfolio.the-full-stack.com,https://architect.portfolio.the-full-stack.com,https://leader.portfolio.the-full-stack.com,https://vibe.portfolio.the-full-stack.com'
```

NO usa Turnstile (el endpoint requiere access JWT, ya autenticado).
NO publica magic-links a SQS para los emails de admin
(`account-disabled`, `account-deleted` no son interactivos —
son notifications). Si lo son, el worker los procesa igual.

## 2. SSM admin-emails

`serverless/lambda/resources/secrets/admin-emails.yaml`:

```yaml
short_name: admin-emails
description: Lista coma-separada de emails admin (whitelist)
type: SecureString
kms_key: alias/portfolio-lambdas
ssm_path: /portfolio/${stage}/admin-emails
source_env_var: ADMIN_EMAILS
local_env_var: ADMIN_EMAILS
rotation_interval_days: 365
consumers:
  - lambda: users
```

Configurar antes del primer deploy:

```bash
# 1. Agregar a docker/env/server/.{dev,stage,prod} (NO commitear)
#    ADMIN_EMAILS=pacg1991@gmail.com

# 2. Sincronizar a SSM
serverless sync-secrets --stage=dev --aws-profile=tfs-dev
# repetir stage + prod

# 3. Verificar
serverless secrets-status --stage=dev
# admin-emails: SKIP (hash match)
```

## 3. Auth_email_worker — plantillas nuevas

Agregar al `auth_email_worker` 3 plantillas + 3 controllers:

```text
serverless/lambda/services/auth_email_worker/core/
├── controllers/email/
│   ├── email_changed.py            # NUEVO
│   ├── account_disabled.py          # NUEVO
│   └── account_deleted.py           # NUEVO
└── templates/
    ├── es/
    │   ├── email-changed.txt
    │   ├── email-changed.html
    │   ├── account-disabled.txt
    │   ├── account-disabled.html
    │   ├── account-deleted.txt
    │   └── account-deleted.html
    └── en/   (mismas 6 plantillas)
```

Modificar `core/settings/operations.py` del worker agregando los
nuevos kinds. Cero impacto en el deploy de `auth`.

Schema del mensaje SQS para los nuevos kinds:

```jsonc
{
  "kind": "email-changed",
  "to": "old@example.com",
  "user_id": "01H9V...",
  "niche": "fintech",
  "subject_id": "auth.profile.email-changed.subject",
  "data": {
    "old_email": "old@example.com",
    "new_email": "new@example.com",
    "changed_at": "2026-05-27T10:00:00Z",
    "revoke_url": "https://api.portfolio.dev.the-full-stack.com/auth?operation=verify&action=revoke-email-change&token=<X>"
  }
}
```

(El `revoke_url` permite undo del cambio si se hizo sin permiso — flow
opcional, no obligatorio en este plan.)

## 4. Cambios al Lambda `auth` (minimos para sessions tracking)

El plan 03 NO crea un PR aparte sobre el lambda `auth`, pero **si
modifica** 1 archivo:

- `services/auth/core/services/session_tracking_service.py` (NUEVO)
- 4 puntos de invocacion (inyectados en):
  - `controllers/register/verify_magic_link.py` (post-emision de
    access+refresh)
  - `controllers/register/verify_code.py`
  - `controllers/login/verify_magic_link.py`, `verify_code.py`,
    `verify_password.py`, `verify_totp.py`
  - `controllers/session/refresh.py` (rotation: UPDATE family_id)
  - `controllers/session/logout.py` (DELETE row)
  - `controllers/webauthn/login_verify.py` (post-emision)
  - `controllers/mfa/recovery_codes_consume.py` (post-emision)

`session_tracking_service.py`:

```python
"""Track sessions activas en `auth_user_sessions`.

Llamado tras CADA emision de refresh JWT (creacion o rotation).
"""

from shared.db import db_session
from shared.db.repositories.auth_users import (
    insert_user_session,
    rotate_session_family_id,
    revoke_session as repo_revoke_session,
)


class SessionTrackingService:
    def on_session_created(self, *, user_id, family_id, ip, country,
                            user_agent) -> None:
        with db_session() as session:
            insert_user_session(
                session,
                user_id=user_id, family_id=family_id,
                device_info=_parse_device_info(user_agent),
                ip=ip, country=country, user_agent=user_agent,
            )

    def on_session_rotated(self, *, old_family_id, new_family_id) -> None:
        with db_session() as session:
            rotate_session_family_id(
                session,
                old_family_id=old_family_id, new_family_id=new_family_id,
            )

    def on_session_revoked(self, *, family_id) -> bool:
        with db_session() as session:
            return repo_revoke_session(session, family_id=family_id)
```

`_parse_device_info(user_agent)` retorna `{browser, browser_version,
os, device_type}` con una lib liviana (ua-parser-light) o regex
custom. Para minimizar deps, regex custom inicial — agregar lib si
necesario.

## 5. Rate-limit rules nuevas (para `/users`)

```bash
# profile.get: 30/min/user_id (lectura)
serverless rate-limit set --stage=dev \
  --endpoint='/users#profile.get' --limit=30 --window=60 \
  --key=user_id --aws-profile=tfs-dev

# profile.update: 10/min/user_id (escritura)
serverless rate-limit set --stage=dev \
  --endpoint='/users#profile.update' --limit=10 --window=60 \
  --key=user_id --aws-profile=tfs-dev

# profile.change-email: 3/h/user_id (sensible)
serverless rate-limit set --stage=dev \
  --endpoint='/users#profile.change-email' --limit=3 --window=3600 \
  --key=user_id --aws-profile=tfs-dev

# profile.delete-account: 2/h/user_id (super sensible)
serverless rate-limit set --stage=dev \
  --endpoint='/users#profile.delete-account' --limit=2 --window=3600 \
  --key=user_id --aws-profile=tfs-dev

# status.* : 60/min/user_id
serverless rate-limit set --stage=dev \
  --endpoint='/users#status' --limit=60 --window=60 \
  --key=user_id --aws-profile=tfs-dev

# admin.list-users: 30/min/user_id (admin)
# admin.* otros: 60/min/user_id
serverless rate-limit set --stage=dev \
  --endpoint='/users#admin' --limit=60 --window=60 \
  --key=user_id --aws-profile=tfs-dev
```

Repetir para `stage` y `prod`.

## 6. CI auto-detect

`change_detector.py` auto-detecta:
- `services/users/` -> redeploy `users`
- `shared/auth/admin.py` -> redeploy `users` (y posiblemente auth si
  decidimos importar `admin.py` desde auth — no necesario en este
  plan)
- `shared/db/models/auth/` (modelos nuevos) -> redeploy auth + users +
  db (migration)
- `services/auth/` (sessions tracking inyectado en 8 archivos) ->
  redeploy `auth`

CI matrix se arma automaticamente.

## 7. Orden de provisioning

```bash
# 1. Aplicar migration 00000004
serverless run --stage=dev --lambda=db --event=events/migrate.json --aws-profile=tfs-dev

# 2. SSM admin-emails
serverless provision-infra --stage=dev --aws-profile=tfs-dev
serverless sync-secrets --stage=dev --aws-profile=tfs-dev

# 3. Deploy auth (con sessions tracking) + auth_email_worker (3 plantillas nuevas)
serverless deploy --lambda=auth --stage=dev --aws-profile=tfs-dev
serverless deploy --lambda=auth_email_worker --stage=dev --aws-profile=tfs-dev

# 4. Deploy users
serverless deploy --lambda=users --stage=dev --aws-profile=tfs-dev

# 5. Seed rate-limit rules
# ... ver bloque rate-limit arriba

# 6. Smoke E2E (ver verificacion-e2e.md)
```
