# 04. Infraestructura — DynamoDB webauthn-challenges + IAM KMS update

## Resumen

| Recurso | Archivo | Que es |
|---------|---------|--------|
| DynamoDB `portfolio-webauthn-challenges-${stage}` | `resources/dynamodb/webauthn-challenges.yaml` | Challenges efimeros (TTL 5 min) |
| KMS key existente `alias/portfolio-lambdas` | (sin cambios) | Para cifrar el TOTP secret via `kms:Encrypt` (CMK directa, decision 1) |
| IAM update Lambda `auth` | (via manifest) | Agregar permisos `kms:Encrypt` + `kms:Decrypt` + DDB nuevo + tablas Neon nuevas |

NO se crean SSM nuevos. NO se crea SQS nueva. La cola
`auth-email-queue` del plan 01 ya alcanza para los emails MFA
(setup-totp-confirmation, recovery-codes-issued, mfa-disabled-alert).

NO se crea Lambda nuevo: todo va al Lambda `auth` existente.

## 1. DynamoDB — `portfolio-webauthn-challenges-${stage}`

`serverless/lambda/resources/dynamodb/webauthn-challenges.yaml`:

```yaml
kind: dynamodb-table
name: portfolio-webauthn-challenges-${stage}
billing_mode: PAY_PER_REQUEST
hash_key:
  name: challenge_id
  type: S
range_key: null
stream: null
ttl_attribute: expires_at
encryption: true
publishes_ssm:
  name: /portfolio/${stage}/dynamodb/webauthn-challenges/name
  arn: /portfolio/${stage}/dynamodb/webauthn-challenges/arn
tags:
  Project: portfolio
  Module: auth-mfa
  ManagedBy: devtools
```

**Schema de item**:

```jsonc
{
  "challenge_id": "01H9X..uuidv7",     // PK
  "user_id": "01H9V..uuidv7",
  "kind": "register",                   // 'register' | 'login'
  "state_b64": "...",                   // fido2 state (bytes -> b64)
  "created_at": 1717000000,
  "expires_at": 1717000300              // TTL attribute, +5min
}
```

**Operaciones**:

- `PutItem` al construir options (register/login).
- `GetItem` + `DeleteItem` (transactional) al verificar.

## 2. IAM update — Lambda `auth` manifest

`serverless/lambda/services/auth/manifest.yaml` — agregar a `uses`:

```yaml
uses:
  # ... existente del plan 01
  tables:
    # ... existentes
    webauthn-challenges: read-write       # NUEVO
  kms:
    - alias: portfolio-lambdas
      actions: [Encrypt, Decrypt]         # NUEVO — CMK directa (NO GenerateDataKey)
```

**Spike-first obligatorio (decision 12 del README)**: ANTES de redactar
el codigo de PR 4, ejecutar `python devtools/run.py serverless
deploy --lambda=auth --stage=dev --dry-run --aws-profile=tfs-dev` con
un `manifest.yaml` que ya declare el bloque `uses.kms`. Tres
escenarios:

1. **Provisioner soporta `uses.kms` declarativo**: declarar como
   arriba, sin cambios en devtools. PR 4 trae solo el cambio al
   manifest.
2. **Provisioner NO soporta `uses.kms`, refactor < 200 lineas + tests
   chicos**: hacerlo dentro de PR 4 (commit 4.2). Es la opcion mas
   probable segun la arquitectura actual del provisioner.
3. **Provisioner requiere refactor mayor (>200 lineas, tests
   estructurales)**: sacar a un plan devtools-aparte. PR 4 se
   reemplaza por inline policy declarada en el shape ya soportado
   (`uses.iam_extra_policies` o equivalente actual). Anotar la
   decision en el body de PR 4 + crear issue del plan devtools.

El spike toma 30 minutos. Su resultado decide cual de los 3 caminos.

## 3. Update al SSM (catalogo de secretos)

NO se crean SSM nuevos. El `jwt-secret` del plan 01 alcanza.

Opcional: si en el futuro se decide tener una KMS key dedicada SOLO
para cifrar el TOTP secret (separada de la del SSM SecureString),
se crearia con un YAML similar a:

```yaml
# OPCIONAL — futuro
kind: kms-key
alias: portfolio-totp
description: KMS key dedicada para cifrar el TOTP secret (CMK directa)
key_spec: SYMMETRIC_DEFAULT
key_usage: ENCRYPT_DECRYPT
rotation: true     # rotacion automatica anual
publishes_ssm:
  arn: /portfolio/${stage}/kms/totp/arn
```

Decision: reusar `alias/portfolio-lambdas` por simplicidad (zero costo
adicional). Si se quiere separar, es un commit independiente y futuro.

## 4. Env vars nuevas (manifest)

```yaml
env:
  default:
    # ... existentes
    KMS_TOTP_KEY_ID: alias/portfolio-lambdas   # NUEVO — para kms:Encrypt CMK directa del TOTP secret
    WEBAUTHN_RP_NAME: 'The Full Stack Portfolio'
  dev:
    WEBAUTHN_RP_ID: portfolio.dev.the-full-stack.com
    WEBAUTHN_ALLOWED_ORIGINS: 'https://portfolio.dev.the-full-stack.com,https://hub.portfolio.dev.the-full-stack.com,https://fintech.portfolio.dev.the-full-stack.com,https://architect.portfolio.dev.the-full-stack.com,https://leader.portfolio.dev.the-full-stack.com,https://vibe.portfolio.dev.the-full-stack.com,http://localhost:9970'
  stage:
    WEBAUTHN_RP_ID: portfolio.stage.the-full-stack.com
    WEBAUTHN_ALLOWED_ORIGINS: 'https://portfolio.stage.the-full-stack.com,https://hub.portfolio.stage.the-full-stack.com,https://fintech.portfolio.stage.the-full-stack.com,https://architect.portfolio.stage.the-full-stack.com,https://leader.portfolio.stage.the-full-stack.com,https://vibe.portfolio.stage.the-full-stack.com'
  prod:
    WEBAUTHN_RP_ID: the-full-stack.com
    WEBAUTHN_ALLOWED_ORIGINS: 'https://the-full-stack.com,https://www.the-full-stack.com,https://portfolio.the-full-stack.com,https://hub.portfolio.the-full-stack.com,https://fintech.portfolio.the-full-stack.com,https://architect.portfolio.the-full-stack.com,https://leader.portfolio.the-full-stack.com,https://vibe.portfolio.the-full-stack.com'
```

Notar: el `WEBAUTHN_RP_ID` es **distinto** entre dev/stage/prod porque
WebAuthn no puede tener un RP_ID que no sea sufijo del origin. Por eso
en prod usamos el apex `the-full-stack.com` (cubre todos los subdomains),
pero en dev/stage usamos `portfolio.dev.the-full-stack.com` /
`portfolio.stage.the-full-stack.com`. **Implicancia**: passkeys
registrados en dev NO funcionan en prod (y viceversa) — es esperado y
correcto.

## 5. Rate-limit rules nuevas

**Decision 13 del README**: TODAS las reglas de rate-limit usan
`IP` como key. NO `user_id`. Razones:

- `shared.rate_limit` actual SOLO soporta keys por IP (sliding
  window weighted, ver skill `serverless-rate-limit`). Soporte para
  custom keys es un plan devtools separado, fuera de scope.
- Rate-limit por `user_id` antes de password-validate filtra info
  (un atacante mide el rate-limit para enumerar emails validos).
  Rate-limit por IP no tiene este problema.

```bash
# mfa.setup-totp: 3/h/IP (raro setear, no debe brute force)
serverless rate-limit set --stage=dev \
  --endpoint='/auth#mfa.setup-totp' --limit=3 --window=3600 --aws-profile=tfs-dev

# mfa.confirm-totp: 10/min/IP (brute force del code TOTP ya esta cubierto
# por las 3 intentos de AC-3 — el rate-limit es defense in depth)
serverless rate-limit set --stage=dev \
  --endpoint='/auth#mfa.confirm-totp' --limit=10 --window=60 --aws-profile=tfs-dev

# mfa.recovery-codes-consume: 5/min/IP
serverless rate-limit set --stage=dev \
  --endpoint='/auth#mfa.recovery-codes-consume' --limit=5 --window=60 --aws-profile=tfs-dev

# webauthn.register-options: 10/min/IP
serverless rate-limit set --stage=dev \
  --endpoint='/auth#webauthn.register-options' --limit=10 --window=60 --aws-profile=tfs-dev

# webauthn.login-options: 20/min/IP (mas alto, mas legitimo)
serverless rate-limit set --stage=dev \
  --endpoint='/auth#webauthn.login-options' --limit=20 --window=60 --aws-profile=tfs-dev

# webauthn.login-verify: 10/min/IP
serverless rate-limit set --stage=dev \
  --endpoint='/auth#webauthn.login-verify' --limit=10 --window=60 --aws-profile=tfs-dev

# login.verify-totp: 10/min/IP (defense in depth — el temp JWT step=2 ya
# requiere haber pasado password; aqui solo limitamos brute force adicional)
serverless rate-limit set --stage=dev \
  --endpoint='/auth#login.verify-totp' --limit=10 --window=60 --aws-profile=tfs-dev

# login.verify-password: 30/min/IP. La proteccion principal contra brute
# force por user es el lock-out de cuenta (failed_attempts) del plan 01,
# que SI usa user_id (es un contador en auth_users, no rate-limit).
serverless rate-limit set --stage=dev \
  --endpoint='/auth#login.verify-password' --limit=30 --window=60 --aws-profile=tfs-dev
```

**Compensacion** (la perdida del rate-limit por user_id): el contador
`auth_users.failed_attempts` del plan 01 sigue siendo el mecanismo
principal de proteccion por user (lock-out tras N intentos fallidos).
El rate-limit por IP es defense in depth, no la primera linea.

## 6. CI auto-detect

`change_detector.py` auto-detecta:
- Cambios en `shared/auth/` -> redeploy auth.
- Cambios en `shared/db/models/auth/` -> redeploy auth + db (db por la
  migration).
- Cambios en `services/auth/` -> redeploy auth.

Sin cambios en `deploy-backend.yml`.

## 7. Orden de provisioning

```bash
# 1. Aplicar migration 00000003
serverless run --stage=dev --lambda=db --event=events/migrate.json --aws-profile=tfs-dev

# 2. Crear DDB nueva
serverless provision-infra --stage=dev --aws-profile=tfs-dev

# 3. Actualizar manifest (IAM kms) y redeploy auth
serverless deploy --lambda=auth --stage=dev --aws-profile=tfs-dev

# 4. Seed rate-limit rules nuevas (8 reglas)
# ... ver bloque arriba

# 5. (Opcional) Setear el primer passkey y TOTP para Pablo en dev como smoke test manual
```
