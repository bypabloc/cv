# 04. Infraestructura — DynamoDB webauthn-challenges + IAM KMS update

## Resumen

| Recurso | Archivo | Que es |
|---------|---------|--------|
| DynamoDB `portfolio-webauthn-challenges-${stage}` | `resources/dynamodb/webauthn-challenges.yaml` | Challenges efimeros (TTL 5 min) |
| KMS key existente `alias/portfolio-lambdas` | (sin cambios) | Para envelope encryption del TOTP secret |
| IAM update Lambda `auth` | (via manifest) | Agregar permisos `kms:GenerateDataKey` + `kms:Decrypt` + DDB nuevo + tablas Neon nuevas |

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
      actions: [GenerateDataKey, Decrypt]  # NUEVO
```

El provisioner del repo (segun el snapshot que tengo) ya genera IAM
scoped por table_name del `tables` block. Para `kms`, hay que verificar
si el manifest del repo lo soporta:

- Si SI: declarar como arriba.
- Si NO: agregar IAM inline policy patch en
  `devtools/serverless/provisioner.py` (cambio fuera de scope estricto
  del plan auth — proponer como T-aparte).

**Decision**: revisar `provisioner.py`. Si no soporta `kms` declarativo,
implementarlo en este plan (1 commit operativo). Es una extension del
shape del manifest, no cambia el contrato existente.

## 3. Update al SSM (catalogo de secretos)

NO se crean SSM nuevos. El `jwt-secret` del plan 01 alcanza.

Opcional: si decidimos en el futuro tener una KMS key dedicada SOLO
para envelope encryption de TOTP (separada de la del SSM SecureString),
se crearia con un YAML similar a:

```yaml
# OPCIONAL — futuro
kind: kms-key
alias: portfolio-totp-envelope
description: KMS key para envelope encryption del TOTP secret
key_spec: SYMMETRIC_DEFAULT
key_usage: ENCRYPT_DECRYPT
rotation: true     # rotacion automatica anual
publishes_ssm:
  arn: /portfolio/${stage}/kms/totp-envelope/arn
```

Decision: reusar `alias/portfolio-lambdas` por simplicidad (zero costo
adicional). Si se quiere separar, es un commit independiente y futuro.

## 4. Env vars nuevas (manifest)

```yaml
env:
  default:
    # ... existentes
    KMS_TOTP_KEY_ID: alias/portfolio-lambdas   # NUEVO — para envelope encryption
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

```bash
# mfa.setup-totp: 3/h/IP (raro setear, no debe brute force)
serverless rate-limit set --stage=dev \
  --endpoint='/auth#mfa.setup-totp' --limit=3 --window=3600 --aws-profile=tfs-dev

# mfa.confirm-totp: 5/min/user_id (no IP) — proteger contra brute force del code TOTP
serverless rate-limit set --stage=dev \
  --endpoint='/auth#mfa.confirm-totp' --limit=5 --window=60 \
  --key=user_id --aws-profile=tfs-dev

# mfa.recovery-codes-consume: 3/min/user_id (no IP)
serverless rate-limit set --stage=dev \
  --endpoint='/auth#mfa.recovery-codes-consume' --limit=3 --window=60 \
  --key=user_id --aws-profile=tfs-dev

# webauthn.register-options: 10/min/IP
serverless rate-limit set --stage=dev \
  --endpoint='/auth#webauthn.register-options' --limit=10 --window=60 --aws-profile=tfs-dev

# webauthn.login-options: 20/min/IP (mas alto, mas legitimo)
serverless rate-limit set --stage=dev \
  --endpoint='/auth#webauthn.login-options' --limit=20 --window=60 --aws-profile=tfs-dev

# webauthn.login-verify: 10/min/IP
serverless rate-limit set --stage=dev \
  --endpoint='/auth#webauthn.login-verify' --limit=10 --window=60 --aws-profile=tfs-dev

# login.verify-totp: 5/min/user_id
serverless rate-limit set --stage=dev \
  --endpoint='/auth#login.verify-totp' --limit=5 --window=60 \
  --key=user_id --aws-profile=tfs-dev

# login.verify-password: 5/min/user_id + 30/min/IP (doble check)
serverless rate-limit set --stage=dev \
  --endpoint='/auth#login.verify-password' --limit=5 --window=60 \
  --key=user_id --aws-profile=tfs-dev
```

Decision: `--key=user_id` requiere que el sistema de rate-limit del
repo soporte keys customizadas (no solo IP). Si NO lo soporta hoy,
implementar el soporte como parte de este plan (extension de
`shared.rate_limit`).

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
