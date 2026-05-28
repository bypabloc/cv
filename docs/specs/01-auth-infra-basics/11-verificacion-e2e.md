# 11. Verificacion E2E iterativa (fase final, gate del PR)

> Ultima fase del plan. Dos partes obligatorias: (A) refactor de tests
> + (B) bateria de comandos reales en bucle "no parar hasta que
> funcione". NO se marca completa con un comando fallando o coverage
> < 80%. Es el gate del PR 9.

## Parte A — refactor de tests

### Que cambia

| Archivo | Accion |
|---------|--------|
| `serverless/lambda/services/auth/tests/integration/*.py` (7 archivos) | CREAR — listados en [06-testing.md](06-testing.md) |
| `serverless/lambda/services/auth/tests/unit/*` | sin cambio (creados en PR 7+8) |
| `serverless/lambda/shared/tests/unit/shared/auth/*` | sin cambio (creados en PR 2) |
| `serverless/lambda/shared/tests/unit/shared/db/repositories/test_auth_*.py` | sin cambio (PR 3) |
| `docs/diagrams/db-er.mmd` | MODIFICAR — agregar cluster `auth_*` |
| `docs/specs/01-auth-infra-basics/` | ELIMINAR (`git rm -r`) — la spec es efimera |

### Barrido global (cero resultados esperados)

```bash
# Ningun test viejo referencia codigo eliminado (no hay eliminacion en este plan)
rg -l "auth_users.*deprecated|legacy_auth|old_jwt" serverless/

# Ningun TODO/FIXME relacionado quedo abierto
rg -l "TODO.*auth|FIXME.*auth|XXX.*auth" serverless/lambda/services/auth/

# La carpeta del plan esta eliminada en el ultimo commit
ls docs/specs/01-auth-infra-basics/ 2>&1 | grep -q "No such file" && echo OK || echo FAIL
```

## Parte B — bateria de comandos reales

Dividida en bloques. Cada bloque debe pasar antes del siguiente.

### Bloque 1 — sintaxis + lint

```bash
# Sintaxis Python global de los nuevos paths
python -m compileall -q \
  serverless/lambda/shared/auth \
  serverless/lambda/shared/db/models/auth \
  serverless/lambda/shared/db/repositories \
  serverless/lambda/services/auth \
  serverless/lambda/services/auth_email_worker

# Lint Python (Ruff)
python devtools/run.py serverless lint --lambda=auth
python devtools/run.py serverless lint --lambda=auth_email_worker
python devtools/run.py serverless lint --shared

# Shared-only imports + dedup D-3
python devtools/run.py serverless lint-deps --lambda=auth
python devtools/run.py serverless lint-deps --lambda=auth_email_worker
python devtools/run.py serverless lint-deps --shared

# Lint del repo (markdown del plan, mientras existe)
pnpm exec biome check serverless/
```

### Bloque 2 — tests unit + coverage

```bash
# Shared (incluye los 17 tests de shared.auth + 10 de repositories.auth)
python devtools/run.py serverless tests --type=unit --shared

# Auth lambda (60+ tests unit)
python devtools/run.py serverless tests --type=unit --lambda=auth
python devtools/run.py serverless tests --type=coverage --lambda=auth
# Verificar: coverage per-file >= 80% en core/services/, core/controllers/,
# core/models/

# Email worker (8 tests)
python devtools/run.py serverless tests --type=unit --lambda=auth_email_worker
python devtools/run.py serverless tests --type=coverage --lambda=auth_email_worker
```

### Bloque 3 — run local (RIE) por endpoint

```bash
# Los eventos de events/ deben dar resultado esperado
python devtools/run.py serverless run --stage=local --lambda=auth \
  --event=events/register-start.json
# Esperado: 200 con {temp_token, user_id, expires_in: 300}

python devtools/run.py serverless run --stage=local --lambda=auth \
  --event=events/register-verify-code.json
# Esperado: 400 (code wrong porque el event tiene un code estatico) o
# 200 si el event refleja un code valido seedeado

python devtools/run.py serverless run --stage=local --lambda=auth \
  --event=events/login-start.json
# Esperado: 404 EMAIL_NOT_FOUND con suggest_register=true

python devtools/run.py serverless run --stage=local --lambda=auth \
  --event=events/session-refresh.json
# Esperado: 401 (token expirado en el event estatico)

# Worker
python devtools/run.py serverless run --stage=local --lambda=auth_email_worker \
  --event=events/register-magic-link.json
# Esperado: log "email.sent.register-magic-link" + return OK
```

### Bloque 4 — migration end-to-end en branch Neon

```bash
# 1. Crear branch
neon branches create --name verify-auth-plan --parent main

# 2. Apuntar DATABASE_URL al branch (extraer del Neon CLI output)
BRANCH_URL="$(neon connection-string verify-auth-plan)"

# 3. Run migration UP
DATABASE_URL="$BRANCH_URL" \
  serverless run --stage=local --lambda=db --event=events/migrate.json

# 4. Verificar tablas
DATABASE_URL="$BRANCH_URL" \
  serverless run --stage=local --lambda=db --event=events/tables.json | \
  grep -E "auth_(users|credentials|email_codes|magic_links|audit_log)"

# 5. Run DOWN -1
DATABASE_URL="$BRANCH_URL" \
  serverless run --stage=local --lambda=db --event=events/downgrade.json

# 6. Re-run UP (idempotencia)
DATABASE_URL="$BRANCH_URL" \
  serverless run --stage=local --lambda=db --event=events/migrate.json

# 7. Cleanup
neon branches delete verify-auth-plan
```

AC verificada: **AC-15**.

### Bloque 5 — tests integration con AWS dev

(Requiere acceso a AWS dev y al branch Neon dev.)

```bash
# Asegurar deploy actualizado
python devtools/run.py serverless deploy --lambda=auth_email_worker --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless deploy --lambda=auth --stage=dev --aws-profile=tfs-dev

# Migration aplicada en dev
python devtools/run.py serverless run --stage=dev --lambda=db \
  --event=events/migrate.json --aws-profile=tfs-dev
python devtools/run.py serverless run --stage=dev --lambda=db \
  --event=events/current.json --aws-profile=tfs-dev
# Esperado: revision 00000002

# Tests integration
python devtools/run.py serverless tests --type=integration --lambda=auth
```

### Bloque 6 — smoke E2E HTTP en dev

```bash
# Variables (no commitear)
API="https://api.portfolio.dev.the-full-stack.com/auth"
EMAIL="test-$(date +%s)@example.com"
TURNSTILE_BYPASS="$(grep -m1 '^TURNSTILE_BYPASS_SECRET=' docker/env/server/.dev | cut -d= -f2-)"

# 1. register.start (con bypass de Turnstile en dev)
RESP=$(curl -sS -X POST "$API" \
  -H "Content-Type: application/json" \
  -H "X-Turnstile-Bypass-Secret: $TURNSTILE_BYPASS" \
  -d "{
    \"operation\": \"register\",
    \"action\": \"start\",
    \"data\": {
      \"email\": \"$EMAIL\",
      \"cf_turnstile_response\": \"\"
    }
  }")
echo "$RESP" | jq .
TEMP_TOKEN=$(echo "$RESP" | jq -r .data.temp_token)
USER_ID=$(echo "$RESP" | jq -r .data.user_id)

# Verificar: code = 0 (success), temp_token presente, expires_in = 300
# AC-1 verificada

# 2. Confirmar que se publico mensaje SQS (CloudWatch del worker)
sleep 5
aws logs tail /aws/lambda/portfolio-auth-email-worker-dev \
  --since 1m --region us-east-1 \
  --filter-pattern '"email.sent.register-magic-link"' --aws-profile tfs-dev

# 3. login.start con email inexistente -> 404 + suggest_register
RESP=$(curl -sS -X POST "$API" \
  -H "Content-Type: application/json" \
  -H "X-Turnstile-Bypass-Secret: $TURNSTILE_BYPASS" \
  -d '{
    "operation": "login",
    "action": "start",
    "data": {
      "email": "noexiste-XXXXXX@example.com",
      "cf_turnstile_response": ""
    }
  }')
echo "$RESP" | jq .
# Esperado: statusCode 404, data.error = EMAIL_NOT_FOUND, data.suggest_register = true
# AC-5 verificada

# 4. Rate-limit: 6ta request a login.start desde misma IP en 60s -> 429
for i in 1 2 3 4 5 6; do
  curl -sS -o /dev/null -w "%{http_code}\n" -X POST "$API" \
    -H "Content-Type: application/json" \
    -H "X-Turnstile-Bypass-Secret: $TURNSTILE_BYPASS" \
    -d '{"operation":"login","action":"start","data":{"email":"a@b.com","cf_turnstile_response":""}}'
done
# Esperado: 5x [200 o 404] + 1x 429
# AC-13 verificada

# 5. Sin Turnstile token ni bypass -> 403
curl -sS -X POST "$API" \
  -H "Content-Type: application/json" \
  -d '{"operation":"register","action":"start","data":{"email":"x@y.com","cf_turnstile_response":""}}' \
  | jq .data.error
# Esperado: TURNSTILE_FAILED
# AC-12 verificada
```

### Bloque 7 — verificacion del PR 9 (cierre)

```bash
# 1. La spec esta eliminada
test ! -d docs/specs/01-auth-infra-basics && echo "spec borrada" || echo "FAIL"

# 2. El ER tiene el cluster auth
grep -q "auth_users" docs/diagrams/db-er.mmd && echo "ER actualizado" || echo "FAIL"

# 3. La rule + skill estan presentes
test -f .claude/rules/auth-system.md && echo "rule OK" || echo "FAIL"
test -f .claude/skills/auth-system/SKILL.md && echo "skill OK" || echo "FAIL"

# 4. La validacion de la skill
claude --permission-mode bypassPermissions \
  --disallowedTools "WebSearch" "WebFetch" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json \
  -p "como funciona el flujo de magic link en el portfolio" 2>&1 | tail -10
# Esperado: num_turns > 1 (skill activada)
```

## Parte C — bucle de correccion ("no parar hasta que funcione")

```text
ejecutar bloque N
   |
   v
{pasa todo?}--si--> bloque N+1
   |
   no
   |
   v
diagnosticar (leer stderr, logs CloudWatch, queries DB)
   |
   v
corregir codigo / test / config
   |
   v
re-ejecutar el bloque que fallo + bloques previos relevantes
   |
   +-----------> volver a "ejecutar bloque N"
```

### Errores tipicos y su correccion

| Sintoma | Diagnostico | Correccion |
|---------|-------------|------------|
| `serverless tests` falla con `ImportError: shared.auth` | uv lock desactualizado en el lambda | `cd serverless/lambda/services/auth && uv sync` |
| `verify_jwt` falla con `Signature verification failed` | JWT_SECRET en local != el usado al firmar | `serverless secrets-status --stage=local` y resincronizar |
| `lint-deps` reporta dep duplicada | El lambda declaro algo que `shared.auth` ya aporta | Retirar la dep del `pyproject.toml` del lambda |
| `register.start` falla con `TURNSTILE_FAILED` aun con bypass | El header `X-Turnstile-Bypass-Secret` no llega | Verificar CORS_ALLOWED_ORIGINS + Postman config |
| Migration falla con `relation cv_profiles does not exist` | El branch Neon no tiene el schema base | Crear desde `main` con `--parent main` |
| `429 RATE_LIMITED` siempre, incluso primera request | Regla de rate-limit con limit=0 o IP whitelisted erronea | `serverless rate-limit list --stage=dev` y corregir |
| GSI `by_family_id` no responde a Query | El index aun esta `BUILDING` | Esperar 1-3 min tras `provision-infra` |
| `arg parse error: --aws-profile` | comando viejo o tipeo | Usar la forma con `=` (`--aws-profile=tfs-dev`) |

## Regla de cierre

Esta fase NO se marca completa mientras:

- Algun bloque (1 a 7) falle,
- Algun test este rojo,
- Coverage per-file < 80% en `core/services/` o `core/controllers/`,
- La carpeta `docs/specs/01-auth-infra-basics/` siga viva en el commit
  final del PR 9.

Iterar — corregir, re-ejecutar, repetir — hasta que toda la bateria
pase. Solo entonces:

1. `git add -A && git commit -m "chore(specs): elimina la carpeta efimera del plan"` (incluye el `git rm -r` y los ajustes finales).
2. `git push -u origin feature/auth-infra-basics-9-verificacion-e2e`.
3. `gh pr create --base dev --title "chore(specs): verificacion E2E + cierre del plan auth-infra-basics" --body "$(cat <<'EOF'`...

`gh pr merge --merge --delete-branch` solo cuando la CI verde + el
reviewer aprobo.

## Promocion dev -> stage -> main

Tras PR 9 mergeado a `dev`:

```bash
# Promover a stage
gh pr create --base stage --head dev --title "chore: promover plan-01-auth-infra-basics a stage"
gh pr merge --merge  # NO --delete-branch (stage es permanente)

# Promover a main
gh pr create --base main --head stage --title "chore: promover plan-01-auth-infra-basics a main"
gh pr merge --merge
```

Tras cada promocion, CI ejecuta `deploy-backend.yml` con auto-detect
de los lambdas afectados (`auth`, `auth_email_worker`, `db` por la
migration que ya esta aplicada — el workflow corre `migrate-db` antes
de redeploy).

Verificacion post-prod:

```bash
# Smoke check en prod (sin Turnstile bypass — Turnstile real)
curl -sS -X POST "https://api.portfolio.the-full-stack.com/auth" \
  -H "Content-Type: application/json" \
  -d '{"operation":"login","action":"start","data":{"email":"smoke-prod-$(date +%s)@example.com","cf_turnstile_response":"<token-real-cliente>"}}'
# Esperado: 404 EMAIL_NOT_FOUND (probablemente, si el email no existe)
```

## Pendientes que el PR 9 NO cubre

(quedan para plan 02-auth-mfa o plan 03-auth-users-management):

- Configurar MFA (TOTP setup, WebAuthn registration).
- CRUD de usuarios (profile/status/admin).
- UI Astro de signup/signin/verify.
- Password reset flow completo (los emails de `password-reset` ya
  estan en el worker; el handler de `verify.set-password` ya existe;
  pero el endpoint POST `/auth?operation=verify&action=request-password-reset`
  se agrega en plan 02 o 03 segun convenga).

Estos pendientes se documentan en el body del PR 9 bajo `## TODO`.
