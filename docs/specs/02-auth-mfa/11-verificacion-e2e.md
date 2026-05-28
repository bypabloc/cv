# 11. Verificacion E2E iterativa — plan 02

> Ultima fase. Gate del PR 8.

## Parte A — refactor de tests

| Archivo | Accion |
|---------|--------|
| `services/auth/tests/integration/test_mfa_*.py` (3) | CREAR |
| `services/auth/tests/integration/test_webauthn_*.py` (2) | CREAR |
| `services/auth/tests/integration/test_login_with_password_and_mfa_e2e.py` | CREAR |
| `services/auth/tests/integration/test_migration_00000003_up_down_e2e.py` | CREAR |
| `services/auth/tests/integration/test_totp_secret_at_rest_encrypted_e2e.py` | CREAR |
| `services/auth/tests/unit/...` | sin cambios (creados en PRs 5-7) |
| `services/auth/tests/unit/controllers/login/test_login_start_*.py` (plan 01) | revisar — algunos pueden necesitar adaptarse al nuevo body con `password` opcional |
| `docs/diagrams/db-er.mmd` | MODIFICAR |
| `docs/specs/02-auth-mfa/` | ELIMINAR |

### Barrido global

```bash
# Tests del plan 01 con `password` en body — verificar que NO romperon
rg -l "password" serverless/lambda/services/auth/tests/unit/controllers/login/

# Codigo eliminado (no aplica — este plan no elimina nada)
rg -l "deprecated_totp|legacy_mfa" serverless/

# TODOs/FIXMEs del scope
rg -l "TODO.*mfa|FIXME.*webauthn|TODO.*passkey" serverless/lambda/services/auth/
```

## Parte B — bateria de comandos reales

### Bloque 1 — sintaxis + lint

```bash
python -m compileall -q \
  serverless/lambda/shared/auth \
  serverless/lambda/shared/aws \
  serverless/lambda/shared/db/models/auth \
  serverless/lambda/shared/db/repositories \
  serverless/lambda/services/auth

python devtools/run.py serverless lint --lambda=auth
python devtools/run.py serverless lint --shared

python devtools/run.py serverless lint-deps --lambda=auth
python devtools/run.py serverless lint-deps --shared
# Esperado: shared.auth ahora declara pyotp+fido2+cryptography+segno
# Lambda auth NO duplica (D-3 OK)
```

### Bloque 2 — tests unit + coverage

```bash
python devtools/run.py serverless tests --type=unit --shared
python devtools/run.py serverless tests --type=unit --lambda=auth
python devtools/run.py serverless tests --type=coverage --lambda=auth
# Verificar coverage per-file >= 85% en controllers/{mfa,webauthn,login}/
# y >= 95% en shared/auth/{totp,webauthn,recovery_codes,encryption}.py
```

### Bloque 3 — run local (RIE) por endpoint nuevo

```bash
# mfa.setup-totp requires un access JWT valido en _meta.authorization
# El event JSON debe traer un JWT generado en setup local
python devtools/run.py serverless run --stage=local --lambda=auth \
  --event=events/mfa-setup-totp.json
# Esperado: 200 con secret_b32 + otpauth_url + qr_code_svg

python devtools/run.py serverless run --stage=local --lambda=auth \
  --event=events/mfa-confirm-totp.json
# Esperado: 204 (o 400 si el code del event esta vencido)

python devtools/run.py serverless run --stage=local --lambda=auth \
  --event=events/webauthn-register-options.json
# Esperado: 200 con challenge_id + options.publicKey.{challenge, rp.id, user.id}

python devtools/run.py serverless run --stage=local --lambda=auth \
  --event=events/login-verify-password.json
# Esperado: 200 con temp_token (step=2) o access+refresh si no MFA
```

### Bloque 4 — migration en branch Neon

```bash
neon branches create --name verify-mfa-plan --parent main
BRANCH_URL="$(neon connection-string verify-mfa-plan)"

# Aplicar 00000002 y 00000003 sequentially
DATABASE_URL="$BRANCH_URL" \
  serverless run --stage=local --lambda=db --event=events/migrate.json

# Verificar tablas auth_mfa_*
DATABASE_URL="$BRANCH_URL" \
  serverless run --stage=local --lambda=db --event=events/tables.json | \
  grep -E "auth_(mfa_methods|mfa_recovery_codes|webauthn_credentials)"

# down -1 (vuelve a 00000002)
DATABASE_URL="$BRANCH_URL" \
  serverless run --stage=local --lambda=db --event=events/downgrade.json

# up de nuevo (idempotencia)
DATABASE_URL="$BRANCH_URL" \
  serverless run --stage=local --lambda=db --event=events/migrate.json

neon branches delete verify-mfa-plan
```

AC verificada: **AC-23**.

### Bloque 5 — integration tests con AWS dev

```bash
# Asegurar deploys actualizados
serverless deploy --lambda=auth --stage=dev --aws-profile=tfs-dev

# Migration aplicada en dev
serverless run --stage=dev --lambda=db --event=events/migrate.json --aws-profile=tfs-dev
serverless run --stage=dev --lambda=db --event=events/current.json --aws-profile=tfs-dev
# Esperado: revision 00000003

# Integration tests
python devtools/run.py serverless tests --type=integration --lambda=auth
```

### Bloque 6 — smoke E2E HTTP en dev

```bash
API="https://api.portfolio.dev.the-full-stack.com/auth"
TURNSTILE_BYPASS="$(grep -m1 '^TURNSTILE_BYPASS_SECRET=' docker/env/server/.dev | cut -d= -f2-)"

# 1. Crear user y obtener access JWT (asumiendo flow del plan 01 ya
#    expuesto en dev)
EMAIL="mfa-smoke-$(date +%s)@example.com"

# Skip toda la fase de register/verify (se asume flow del plan 01
# funcional). Para el smoke, usar el endpoint
# (futuro) /auth#admin.create-test-user que NO existe.
# Alternativa: completar el flow manualmente via curl.

# Aqui se asume que se tiene un ACCESS_TOKEN valido en variable
ACCESS="<access-token-obtenido-del-flow-de-plan-01>"

# 2. mfa.setup-totp
curl -sS -X POST "$API" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"operation":"mfa","action":"setup-totp","data":{}}' | jq .
# Esperado: data.secret_b32 (string base32), data.otpauth_url, data.qr_code_svg
# AC-1 verificada

# 3. mfa.confirm-totp con code generado por pyotp
SECRET="<secret_b32 obtenido>"
CODE=$(python -c "import pyotp; print(pyotp.TOTP('$SECRET').now())")
curl -sS -X POST "$API" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d "{\"operation\":\"mfa\",\"action\":\"confirm-totp\",\"data\":{\"code\":\"$CODE\"}}"
# Esperado: 204
# AC-2 verificada

# 4. mfa.recovery-codes-generate
curl -sS -X POST "$API" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"operation":"mfa","action":"recovery-codes-generate","data":{}}' | jq .data
# Esperado: data.codes -> array de 10 strings 10 chars cada uno
# AC-7 verificada

# 5. Verificar at-rest encryption del TOTP secret
# (consulta directa a Neon — la lambda no lo expone)
psql "<DATABASE_URL del branch dev>" \
  -c "SELECT user_id, encode(totp_secret_ciphertext, 'hex') FROM auth_mfa_methods WHERE kind='totp' LIMIT 1;"
# Esperado: ciphertext en hex, NO el secret_b32 plain
# AC-24 verificada
```

### Bloque 7 — verificacion del PR 8 (cierre)

```bash
# 1. spec eliminada
test ! -d docs/specs/02-auth-mfa && echo "OK" || echo "FAIL"

# 2. ER actualizado
grep -q "auth_mfa_methods" docs/diagrams/db-er.mmd && echo "ER OK"
grep -q "auth_webauthn_credentials" docs/diagrams/db-er.mmd && echo "ER OK"

# 3. Skill auth-system tiene keywords MFA
grep -q "totp\|webauthn\|passkey\|mfa" .claude/skills/auth-system/SKILL.md && echo "skill OK"

# 4. Validacion skill
claude --permission-mode bypassPermissions \
  --disallowedTools "WebSearch" "WebFetch" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json \
  -p "como funciona webauthn passkeys en el portfolio" 2>&1 | tail -10
# Esperado: num_turns > 1
```

## Parte C — bucle de correccion

```text
ejecutar bloque N
   |
   v
{paso?}--si--> bloque N+1
   |
   no
   |
   v
diagnosticar (logs CloudWatch + tail de tests + queries DB)
   |
   v
corregir codigo / test / config
   |
   v
re-ejecutar el bloque que fallo
   |
   +-----------> volver
```

### Errores tipicos

| Sintoma | Diagnostico | Correccion |
|---------|-------------|------------|
| `KMS not authorized to GenerateDataKey` | IAM role del lambda sin `kms:GenerateDataKey` | Verificar `manifest.yaml.uses.kms` esta declarado + provisioner aplica policy |
| `Webauthn challenge expired` aun en < 5min | DDB TTL aplico antes — clock drift | Aumentar TTL a 600s en el commit del scaffold (o ver clock skew Lambda) |
| `Webauthn rp_id mismatch` | `WEBAUTHN_RP_ID` no matchea el `origin` del header | Ajustar env var por stage (apex en prod, subdomain en dev/stage) |
| `pyotp.TOTP(secret).verify(code) returns False` aun con code correcto | Clock drift entre client y server > 30s | `valid_window=1` en `verify_totp_code` (ya esta por default) |
| `Recovery code consumed_at race` | 2 requests concurrentes del mismo code | Usar UPDATE ... WHERE consumed_at IS NULL RETURNING * (atomic) |
| `pyotp ImportError` en lambda | uv lock desactualizado | `cd serverless/lambda/services/auth && uv sync` |
| `lint-deps reporta python-fido2 duplicada` | Lambda declara fido2 ademas de shared.auth | Retirar del pyproject.toml del lambda |
| Migration falla por `auth_users not exists` | branch Neon no tiene plan 01 aplicado | Aplicar 00000002 primero |
| `aws ssm GetParameter access denied` para webauthn-challenges name | provisioner no agrego el SSM path al IAM | Verificar `uses.tables.webauthn-challenges` en el manifest |

## Regla de cierre

NO se marca completa mientras:

- Algun bloque falle,
- Algun test rojo,
- Coverage per-file < 85% en controllers nuevos,
- < 95% en `shared/auth/{totp,webauthn,recovery_codes,encryption}.py`,
- La carpeta `docs/specs/02-auth-mfa/` siga viva.

Iterar hasta verde. Solo entonces:

```bash
git add -A
git commit -m "chore(specs): elimina la carpeta efimera del plan 02-auth-mfa"
git push -u origin feature/auth-mfa-8-verificacion-e2e
gh pr create --base dev --title "chore(specs): verificacion E2E + cierre del plan 02-auth-mfa" --body "..."
```

## Promocion dev -> stage -> main

Tras PR 8 mergeado:

```bash
gh pr create --base stage --head dev --title "chore: promover plan-02-auth-mfa a stage"
gh pr merge --merge
gh pr create --base main --head stage --title "chore: promover plan-02-auth-mfa a main"
gh pr merge --merge
```

CI auto-deploya `auth` con el nuevo codigo + aplica migration en
stage/prod automaticamente (deploy-backend.yml).

## Pendientes que el PR 8 NO cubre

- UI Astro de MFA setup (QR scanner mobile-friendly, WebAuthn JS API
  invoke, recovery codes download).
- Email worker plantillas adicionales (`mfa-confirmed-alert`,
  `mfa-disabled-alert`, `passkey-added-alert`).
- Quedan para planes futuros o se agregan inline al plan 03.

Estos pendientes se documentan en el `## TODO` del PR 8.
