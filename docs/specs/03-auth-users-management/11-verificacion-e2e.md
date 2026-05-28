# 11. Verificacion E2E iterativa — plan 03

> Ultima fase. Gate del PR 9.

## Parte A — refactor de tests

| Archivo | Accion |
|---------|--------|
| `services/users/tests/integration/test_*_e2e.py` (9) | CREAR |
| `services/auth/tests/integration/test_session_tracking_*.py` (4) | CREAR (ya en PR 8) |
| `services/auth/tests/unit/controllers/login/test_*.py` | revisar — verificar que session tracking inyectado no rompe |
| `docs/diagrams/db-er.mmd` | MODIFICAR |
| `docs/specs/03-auth-users-management/` | ELIMINAR |
| `docs/specs/01-auth-infra-basics/` y `docs/specs/02-auth-mfa/` | (ya eliminados al cerrar planes 01 y 02 respectivamente; verificar) |

### Barrido global

```bash
# Tests que referencien funciones eliminadas (no aplica — solo agregamos)
rg -l "deprecated_users|legacy_admin" serverless/

# TODOs/FIXMEs del scope
rg -l "TODO.*users|FIXME.*admin" serverless/lambda/services/users/

# La spec se elimino
test ! -d docs/specs/03-auth-users-management && echo OK || echo FAIL
```

## Parte B — bateria de comandos reales

### Bloque 1 — sintaxis + lint

```bash
python -m compileall -q \
  serverless/lambda/shared/auth \
  serverless/lambda/shared/db/models/auth \
  serverless/lambda/shared/db/repositories \
  serverless/lambda/services/users \
  serverless/lambda/services/auth \
  serverless/lambda/services/auth_email_worker

python devtools/run.py serverless lint --lambda=users
python devtools/run.py serverless lint --lambda=auth
python devtools/run.py serverless lint --lambda=auth_email_worker
python devtools/run.py serverless lint --shared

python devtools/run.py serverless lint-deps --lambda=users
python devtools/run.py serverless lint-deps --lambda=auth
python devtools/run.py serverless lint-deps --lambda=auth_email_worker
python devtools/run.py serverless lint-deps --shared
```

### Bloque 2 — tests unit + coverage

```bash
python devtools/run.py serverless tests --type=unit --shared
python devtools/run.py serverless tests --type=unit --lambda=users
python devtools/run.py serverless tests --type=unit --lambda=auth_email_worker
python devtools/run.py serverless tests --type=unit --lambda=auth   # no regresiones
python devtools/run.py serverless tests --type=coverage --lambda=users
# Coverage per-file >= 85% en controllers/{profile,status,admin}/
# y >= 100% en shared/auth/admin.py
```

### Bloque 3 — run local (RIE) por endpoint

```bash
# Profile
python devtools/run.py serverless run --stage=local --lambda=users \
  --event=events/profile-get.json
# Esperado: 200 con profile

python devtools/run.py serverless run --stage=local --lambda=users \
  --event=events/profile-update.json
# Esperado: 200

python devtools/run.py serverless run --stage=local --lambda=users \
  --event=events/profile-change-email.json
# Esperado: 200 con request_id

python devtools/run.py serverless run --stage=local --lambda=users \
  --event=events/profile-delete-account.json
# Esperado: 204

# Status
python devtools/run.py serverless run --stage=local --lambda=users \
  --event=events/status-list-sessions.json
# Esperado: 200 con array

# Admin
python devtools/run.py serverless run --stage=local --lambda=users \
  --event=events/admin-list-users.json
# Esperado: 200 con primeros N + cursor (si caller es admin)
# o 404 NOT_FOUND si no admin

# Email worker
python devtools/run.py serverless run --stage=local --lambda=auth_email_worker \
  --event=events/email-changed.json
# Esperado: log "email.sent.email-changed"
```

### Bloque 4 — migration end-to-end

```bash
neon branches create --name verify-users-plan --parent main
BRANCH_URL="$(neon connection-string verify-users-plan)"

# Aplicar 00000002 + 00000003 + 00000004 secuencial
DATABASE_URL="$BRANCH_URL" \
  serverless run --stage=local --lambda=db --event=events/migrate.json

# Verificar tablas + columnas
DATABASE_URL="$BRANCH_URL" \
  serverless run --stage=local --lambda=db --event=events/tables.json | \
  grep -E "auth_user_(sessions|admin_actions|consent_log)"

psql "$BRANCH_URL" -c "\d auth_users" | grep -E "(display_name|locale|timezone|marketing_consent|deleted_at)"

# Downgrade -1 (vuelve a 00000003)
DATABASE_URL="$BRANCH_URL" \
  serverless run --stage=local --lambda=db --event=events/downgrade.json

# Up de nuevo (idempotencia)
DATABASE_URL="$BRANCH_URL" \
  serverless run --stage=local --lambda=db --event=events/migrate.json

neon branches delete verify-users-plan
```

AC verificada: **AC-25**.

### Bloque 5 — integration tests con AWS dev

```bash
# Asegurar deploys actualizados
serverless deploy --lambda=auth_email_worker --stage=dev --aws-profile=tfs-dev
serverless deploy --lambda=auth --stage=dev --aws-profile=tfs-dev
serverless deploy --lambda=users --stage=dev --aws-profile=tfs-dev

# Migration en dev
serverless run --stage=dev --lambda=db --event=events/migrate.json --aws-profile=tfs-dev
serverless run --stage=dev --lambda=db --event=events/current.json --aws-profile=tfs-dev
# Esperado: revision 00000004

# Tests integration
python devtools/run.py serverless tests --type=integration --lambda=users
python devtools/run.py serverless tests --type=integration --lambda=auth
```

### Bloque 6 — smoke E2E HTTP en dev

```bash
API_AUTH="https://api.portfolio.dev.the-full-stack.com/auth"
API_USERS="https://api.portfolio.dev.the-full-stack.com/users"
TURNSTILE_BYPASS="$(grep -m1 '^TURNSTILE_BYPASS_SECRET=' docker/env/server/.dev | cut -d= -f2-)"

# 1. Crear un user via register + verify (flow del plan 01)
EMAIL="users-smoke-$(date +%s)@example.com"
# ... (curl al flow de plan 01 hasta obtener access_token + refresh_token)
ACCESS="<access-obtenido>"

# 2. profile.get
curl -sS -X POST "$API_USERS" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"operation":"profile","action":"get","data":{}}' | jq .data
# Esperado: data.email = $EMAIL, data.status = 'active', data.mfa_configured = false

# 3. profile.update
curl -sS -X POST "$API_USERS" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"operation":"profile","action":"update","data":{"display_name":"Pablo Smoke","locale":"es","marketing_consent":true}}' | jq .data
# Esperado: data.display_name = "Pablo Smoke", data.locale = "es"
# AC-2, AC-3 verificadas

# 4. status.list-sessions (deberia mostrar 1, la actual)
curl -sS -X POST "$API_USERS" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"operation":"status","action":"list-sessions","data":{}}' | jq '.data | length'
# Esperado: 1
# AC-8 verificada

# 5. admin.list-users con un user NO admin -> 404
curl -sS -o /dev/null -w "%{http_code}\n" -X POST "$API_USERS" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"operation":"admin","action":"list-users","data":{}}'
# Esperado: 404 (porque $EMAIL no esta en ADMIN_EMAILS)
# AC-11 verificada

# 6. profile.delete-account
curl -sS -X POST "$API_USERS" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"operation":"profile","action":"delete-account","data":{"confirm":"DELETE-MY-ACCOUNT"}}'
# Esperado: 204 (o {message: OK, status: 204} en el body)
# AC-6 verificada

# 7. Verificar que el access JWT ya no funciona (blacklisted)
curl -sS -o /dev/null -w "%{http_code}\n" -X POST "$API_USERS" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"operation":"profile","action":"get","data":{}}'
# Esperado: 401 TOKEN_BLACKLISTED

# 8. Intentar register con el mismo email -> AC-27 (re-uso permitido)
curl -sS -X POST "$API_AUTH" \
  -H "Content-Type: application/json" \
  -H "X-Turnstile-Bypass-Secret: $TURNSTILE_BYPASS" \
  -d "{\"operation\":\"register\",\"action\":\"start\",\"data\":{\"email\":\"$EMAIL\",\"cf_turnstile_response\":\"\"}}" | jq .
# Esperado: 201 (email libre porque el viejo esta soft-deleted)
```

### Bloque 7 — smoke admin

Requiere admin (email de Pablo en SSM admin-emails):

```bash
# Login como Pablo (flow del plan 01 + plan 02 con MFA si aplica)
PABLO_ACCESS="<obtenido>"

# admin.list-users
curl -sS -X POST "$API_USERS" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $PABLO_ACCESS" \
  -d '{"operation":"admin","action":"list-users","data":{"page_size":10}}' | jq '.data | {users: .users | length, next_cursor}'
# Esperado: users array + next_cursor presente si hay > 10
# AC-12 verificada

# admin.disable-user (sobre un user creado en bloque anterior)
TARGET="<user_id-obtenido>"
curl -sS -X POST "$API_USERS" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $PABLO_ACCESS" \
  -d "{\"operation\":\"admin\",\"action\":\"disable-user\",\"data\":{\"user_id\":\"$TARGET\",\"reason\":\"smoke test\"}}"
# Esperado: 204
# AC-15 verificada

# El target intenta login -> 403 ACCOUNT_DISABLED
curl -sS -X POST "$API_AUTH" \
  -H "Content-Type: application/json" \
  -H "X-Turnstile-Bypass-Secret: $TURNSTILE_BYPASS" \
  -d "{\"operation\":\"login\",\"action\":\"start\",\"data\":{\"email\":\"<email-del-target>\",\"cf_turnstile_response\":\"\"}}" | jq .
# Esperado: data.error = ACCOUNT_DISABLED
# AC-16 verificada
```

### Bloque 8 — cierre PR 9

```bash
test ! -d docs/specs/03-auth-users-management && echo "spec eliminada"
grep -q "auth_user_sessions" docs/diagrams/db-er.mmd && echo "ER OK"
grep -q "admin\|sessions" .claude/skills/auth-system/SKILL.md && echo "skill OK"

# Skill validation
claude --permission-mode bypassPermissions \
  --disallowedTools "WebSearch" "WebFetch" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json \
  -p "como deshabilitar un usuario en el portfolio" 2>&1 | tail -10
# Esperado: num_turns > 1
```

## Parte C — bucle de correccion

```text
ejecutar bloque N
   |
   v
{paso?}--si--> bloque N+1
   |
   no --> diagnosticar -> corregir -> re-ejecutar -> repetir
```

### Errores tipicos

| Sintoma | Diagnostico | Correccion |
|---------|-------------|------------|
| `admin.list-users` siempre 404 incluso siendo admin | SSM admin-emails vacio o desactualizado | `serverless secrets-status --stage=dev` + sync_secrets |
| `IntegrityError: duplicate key value violates unique constraint ux_auth_users_email_active` | El partial unique no esta como esperado | Verificar migration 00000004 aplicada + el old UNIQUE removido |
| `profile.delete-account` no anonimiza email | Logica del service incorrecta | Verificar `profile_service.soft_delete` — recordar que el soft-delete es UPDATE de `auth_users` mas DELETE explicitos en credentials/mfa/sessions; las FK CASCADE NO se disparan (las cascades reaccionan a DELETE, no a UPDATE) |
| `status.list-sessions` retorna vacio aun con sessions activas | session_tracking_service no se llama o falla silenciosamente | logs CloudWatch + verify_session_tracking en auth (T10) |
| `force-logout` no invalida JWT viejo | Blacklist no se persiste o GSI query falla | Test integration del blacklist family detection |
| Migration 00000004 falla con `cannot add value to enum used by table` | El ALTER TYPE en transaction | Ejecutar el ALTER TYPE fuera de transaction (con autocommit) |

## Regla de cierre

NO se marca completa mientras:

- Algun bloque (1 a 8) falle,
- Algun test rojo (unit, integration, ni del lambda auth tampoco),
- Coverage per-file < 85% en `controllers/{profile,status,admin}/`,
- < 100% en `shared/auth/admin.py`,
- Spec `docs/specs/03-auth-users-management/` sigue viva.

Iterar hasta verde. Solo entonces:

```bash
git add -A
git commit -m "chore(specs): elimina la carpeta efimera del plan 03-auth-users-management"
git push -u origin feature/auth-users-mgmt-9-verificacion-e2e
gh pr create --base dev --title "chore(specs): verificacion E2E + cierre del plan 03-auth-users-management" --body "..."
```

## Promocion dev -> stage -> main

Tras PR 9 mergeado:

```bash
gh pr create --base stage --head dev --title "chore: promover plan-03-auth-users-management a stage"
gh pr merge --merge
gh pr create --base main --head stage --title "chore: promover plan-03-auth-users-management a main"
gh pr merge --merge
```

CI auto-deploya `auth`, `auth_email_worker`, `users` con auto-detect.
La migration 00000004 se aplica via `deploy-backend.yml` `migrate-db`
step antes del deploy de lambdas.

Verificacion post-prod:

```bash
# Smoke check prod
curl -sS -X POST "https://api.portfolio.the-full-stack.com/users" \
  -H "Content-Type: application/json" \
  -d '{"operation":"profile","action":"get","data":{}}'
# Esperado: 401 MISSING_AUTHORIZATION (sin token)
```

## Pendientes que el PR 9 NO cubre (queda para futuro)

- Frontend Astro: signup/signin/dashboard/settings con UI.
- Hard-delete programatico de users soft-deleted >30 dias
  (cron Lambda nuevo, NO en scope).
- Bulk admin operations (import/export CSV).
- Email worker plantilla `revoke-email-change` (undo del cambio si
  fue malicioso) — opcional.

Documentar en `## TODO` del PR 9.
