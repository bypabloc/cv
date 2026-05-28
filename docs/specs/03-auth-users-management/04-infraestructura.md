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
  # publish-only: el Lambda `users` NUNCA invoca SES directamente.
  # Solo publica mensajes a la cola `auth-email-queue`; el
  # `auth_email_worker` consume y manda el email. Por eso
  # `sends-email: false` (no necesita IAM ses:SendEmail) pese a que
  # operativamente algunas actions terminan disparando un email.
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

El plan 03 SI toca el lambda `auth`: agrega **1 archivo nuevo** y
modifica **10 controllers existentes** con una inyeccion minima
(2-3 lineas para llamar al helper).

- `services/auth/core/services/session_tracking_service.py` (NUEVO)
- 10 controllers modificados (post-emision de tokens):
  - `controllers/register/verify_magic_link.py` (post-emision de
    access+refresh — `on_session_created`)
  - `controllers/register/verify_code.py` (`on_session_created`)
  - `controllers/login/verify_magic_link.py` (`on_session_created`)
  - `controllers/login/verify_code.py` (`on_session_created`)
  - `controllers/login/verify_password.py` (`on_session_created`)
  - `controllers/login/verify_totp.py` (`on_session_created`)
  - `controllers/webauthn/login_verify.py` (`on_session_created`)
  - `controllers/mfa/recovery_codes_consume.py` (`on_session_created`)
  - `controllers/session/refresh.py` (rotation: `on_session_rotated`
    con old_family_id + new_family_id)
  - `controllers/session/logout.py` (`on_session_revoked` tras
    blacklist family DDB)

> **Sobre `family_id`**: el refresh JWT del plan 01 ya lleva
> `family_id` en sus claims (uuidv7), generado en
> `register.verify-*` / `login.verify-*` y rotado en
> `session.refresh`. El helper `session_tracking_service` lo recibe
> como argumento; **no necesita inferirlo**. En cada controller del
> lambda `auth`, tras emitir los tokens, el codigo ya tiene en
> memoria el `family_id` viejo (de los claims del refresh entrante,
> solo aplica a `session.refresh`) y el `family_id` nuevo
> (recien generado). Ambos se pasan al helper.

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

> `shared.rate_limit` ya soporta `--key=user_id` desde el plan 02
> (introducido para `mfa.confirm-totp`, `mfa.recovery-codes-consume`,
> etc.). El bucket key se computa con `user_id` extraido del access
> JWT, no de la IP. Si el controller no tiene access JWT, el helper
> hace fallback a IP automaticamente (defensa contra requests
> anonimos que igual quieren rate-limitearse).

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

El **orden es estricto**: `auth` (con sessions tracking) debe estar
deployado ANTES que `users` se exponga, porque
`status.list-sessions` lee de `auth_user_sessions` y esa tabla solo
empieza a poblarse tras el deploy de `auth` con el helper inyectado.

```bash
# 1. Aplicar migration 00000004 (crea auth_user_sessions, etc.)
serverless run --stage=dev --lambda=db --event=events/migrate.json --aws-profile=tfs-dev

# 2. SSM admin-emails
serverless provision-infra --stage=dev --aws-profile=tfs-dev
serverless sync-secrets --stage=dev --aws-profile=tfs-dev

# 3. Deploy auth (con sessions tracking) PRIMERO
#    A partir de aqui, cada nueva sesion (register/login/refresh)
#    inserta o actualiza la row en auth_user_sessions.
serverless deploy --lambda=auth --stage=dev --aws-profile=tfs-dev
serverless deploy --lambda=auth_email_worker --stage=dev --aws-profile=tfs-dev

# 4. Deploy users (lee auth_user_sessions ya poblado por el lambda
#    auth desde el paso 3)
serverless deploy --lambda=users --stage=dev --aws-profile=tfs-dev

# 5. Seed rate-limit rules
# ... ver bloque rate-limit arriba

# 6. Smoke E2E (ver verificacion-e2e.md)
```

> **Sesiones pre-deploy quedan invisibles**: refresh tokens emitidos
> ANTES del deploy de `auth` con session tracking NO tienen row en
> `auth_user_sessions`. Para esos users, `status.list-sessions`
> devuelve vacio hasta que hagan `session.refresh` (que rota family
> y entra al INSERT/UPDATE del helper) o re-login. Es comportamiento
> esperado, no un bug. Documentar en el frontend cuando exista:
> "si la lista de sesiones aparece vacia, hacer logout+login para
> reactivar el tracking".
>
> **Dependencia del integration test multi-device** (AC-8): el test
> `test_status_list_sessions_multi_device_e2e.py` (06-testing)
> requiere que T10 (sessions tracking en auth) ya este deployado
> en dev. La descomposicion en 08 hace WT-C (T9) y WT-D (T10)
> paralelos en codigo, pero **el integration test del paso de E2E
> en `users` depende del deploy de `auth` post-T10**. Reflejar en
> PR 9 (verificacion E2E): correr integration tests SOLO tras
> mergear PR 8.
