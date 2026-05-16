# DEPLOYMENT — Backend serverless del portfolio

> Guia paso a paso del primer deploy del backend en una cuenta AWS nueva.
> Asume que el repo esta clonado y los pre-requisitos estan instalados.
> Para operacion del dia a dia, ver [RUNBOOK.md](RUNBOOK.md).

## Pre-requisitos

| Herramienta | Version minima | Verificar |
|-------------|----------------|-----------|
| AWS CLI | 2.15+ | `aws --version` |
| AWS SAM CLI | 1.160+ | `sam --version` |
| Python | 3.13 | `python3 --version` |
| uv | 0.5+ | `uv --version` |
| Node | 24 | `node --version` |
| pnpm | 11.0.9 | `pnpm --version` |
| psql | 16+ (opcional, para migrations manuales) | `psql --version` |
| jq | 1.6+ | `jq --version` |
| curl | 8+ | `curl --version` |

Instalacion SAM CLI:

```bash
uv tool install aws-sam-cli
```

## Cuentas y servicios externos

Antes de empezar el deploy, completar estos pasos manuales (una vez):

1. **AWS account**
   - Crear sub-account dedicada (recomendado) o usar la principal
   - IAM Identity Center (SSO) configurado con role `AdministratorAccess`
   - Anotar `ACCOUNT_ID` (12 digitos)
2. **Cloudflare Turnstile**
   - Crear widget en https://dash.cloudflare.com -> Turnstile -> Add site
   - Mode: **Managed**
   - Hostnames: los 6 subdominios del portfolio (`the-full-stack.com`,
     `hub.portfolio.the-full-stack.com`, `fintech.portfolio.the-full-stack.com`,
     `architect.portfolio.the-full-stack.com`, `leader.portfolio.the-full-stack.com`,
     `vibe.portfolio.the-full-stack.com`)
   - Anotar `TURNSTILE_SITEKEY` y `TURNSTILE_SECRET`
3. **Neon PostgreSQL**
   - Crear proyecto serverless en https://console.neon.tech
   - Region: AWS us-east-1
   - Postgres 18
   - Crear dos branches: `dev` y `prod` (cada uno con su connection string)
   - Anotar `NEON_URL_DEV` y `NEON_URL_PROD`
4. **AWS SES (production access)**
   - Verificar domain identity en us-east-1
   - Configurar DKIM/SPF/DMARC en Cloudflare DNS (ver
     [docs/ses-setup.md](docs/ses-setup.md))
   - Solicitar production access (24-48h) si no la tienes ya

## Setup inicial (una vez por cuenta)

### 1. Configurar AWS SSO profile

```bash
aws configure sso
# SSO start URL: https://<org>.awsapps.com/start
# SSO region: us-east-1
# Account: <ACCOUNT_ID>
# Role: AdministratorAccess
# Profile name: tfs-dev
```

Test:

```bash
aws sts get-caller-identity --profile tfs-dev
```

### 2. Crear KMS key para SSM SecureString

```bash
aws kms create-key --profile tfs-dev --region us-east-1 \
  --description "Encryption key para SSM Parameters del portfolio backend"
# Anotar el KeyId

aws kms create-alias --profile tfs-dev --region us-east-1 \
  --alias-name alias/portfolio-lambdas \
  --target-key-id <KEY_ID>
```

### 3. Cargar secrets a SSM Parameter Store

Generar password del dashboard:

```bash
DASHBOARD_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
DASHBOARD_HASH=$(python3 -c "import bcrypt; print(bcrypt.hashpw('$DASHBOARD_PASSWORD'.encode(), bcrypt.gensalt(rounds=12)).decode())")
echo "Password (GUARDAR ESTE VALOR): $DASHBOARD_PASSWORD"
```

Guardar parametros:

```bash
PROFILE=tfs-dev
REGION=us-east-1

aws ssm put-parameter --profile $PROFILE --region $REGION \
  --name /portfolio/turnstile-secret \
  --type SecureString --key-id alias/portfolio-lambdas \
  --value "<TURNSTILE_SECRET>"

aws ssm put-parameter --profile $PROFILE --region $REGION \
  --name /portfolio/neon-url \
  --type SecureString --key-id alias/portfolio-lambdas \
  --value "<NEON_URL_DEV>"

aws ssm put-parameter --profile $PROFILE --region $REGION \
  --name /portfolio/owner-email \
  --type String \
  --value "owner@example.com"

aws ssm put-parameter --profile $PROFILE --region $REGION \
  --name /portfolio/ses-from-address \
  --type String \
  --value "no-reply@<dominio-verificado>"

aws ssm put-parameter --profile $PROFILE --region $REGION \
  --name /portfolio/dashboard-password-hash \
  --type SecureString --key-id alias/portfolio-lambdas \
  --value "$DASHBOARD_HASH"
```

Verificar:

```bash
aws ssm get-parameters-by-path --profile $PROFILE --region $REGION \
  --path /portfolio --recursive \
  --query 'Parameters[].[Name,Type]' --output table
```

Inventario completo de SSM Parameters en [docs/secrets.md](docs/secrets.md).

### 4. AWS Billing Alarm (la unica alarma del proyecto)

Habilitar billing alerts (solo us-east-1, una vez por cuenta):

```bash
aws cloudwatch put-metric-alarm --profile $PROFILE --region us-east-1 \
  --alarm-name portfolio-billing-alarm \
  --alarm-description "Costo mensual estimado supera USD 5" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --evaluation-periods 1 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=Currency,Value=USD \
  --alarm-actions <SNS_TOPIC_ARN_OPCIONAL>
```

Si no tienes SNS topic, podes omitir `--alarm-actions` y revisar manual
con `aws cloudwatch describe-alarms`.

## Deploy del stack

### 1. Validar template

```bash
cd serverless/
uv sync
sam validate --lint
```

### 2. Build

```bash
sam build --use-container --parallel
```

`--use-container` compila layers Python en docker imagen Lambda
(garantiza compat con runtime real). `--parallel` builda todas las
funciones en paralelo.

### 3. Deploy a dev

Primer deploy guiado:

```bash
sam deploy --config-env dev --guided --profile tfs-dev
```

Responder:

- Stack Name: `portfolio-backend-dev`
- Region: `us-east-1`
- Confirm changes before deploy: `Y`
- Allow IAM role creation: `Y`
- Disable rollback: `N`
- Save arguments to samconfig: `Y`
- SAM configuration environment: `dev`

Subsiguientes:

```bash
sam deploy --config-env dev --profile tfs-dev
```

### 4. Aplicar migrations Postgres

```bash
cd serverless/
DATABASE_URL="<NEON_URL_DEV>" python scripts/migrate.py up
```

Verificar tablas:

```bash
psql "<NEON_URL_DEV>" -c "\dt portfolio.*"
# Espera: contacts, tracking_events, daily_metrics, top_pages_daily, migrations_log
```

### 5. Smoke test

```bash
./serverless/scripts/smoke_test.sh dev
# Espera "All smoke tests PASSED" + exit code 0
```

### 6. Deploy a stage

Stage es un ambiente de pre-produccion (replica prod). Comparte la config
SSM con dev/prod (`/portfolio/neon-url`, `/portfolio/turnstile-secret`).

```bash
sam deploy --config-env stage --profile tfs-dev
./serverless/scripts/smoke_test.sh stage
```

Crea el stack `portfolio-backend-stage` (REST API `portfolio-api-stage`,
6 Lambdas, 5 tablas DynamoDB con sufijo `-stage`). El parametro `Stage`
de `template.yaml` acepta `dev | stage | prod` y `Mappings.StageConfig`
define la whitelist CORS por ambiente.

### 7. Deploy a prod

Repetir paso 3 con `--config-env prod`. Antes:

- Reemplazar `/portfolio/neon-url` con `NEON_URL_PROD`
  (o usar parameter store con stage suffix si separas)
- Aplicar migrations contra Neon branch prod
- Smoke test contra stage prod

```bash
sam deploy --config-env prod --profile tfs-dev
./serverless/scripts/smoke_test.sh prod
```

## Frontend (Astro 6)

### 1. Configurar env vars publicas

Las vars `PUBLIC_*` son de la categoria `client`. En
`docker/env/client/.dev` y `docker/env/client/.prod`:

```bash
PUBLIC_API_ENDPOINT=https://<api-id>.execute-api.us-east-1.amazonaws.com/dev
PUBLIC_TURNSTILE_SITEKEY=<TURNSTILE_SITEKEY>
```

Reemplazar `<api-id>` con el output `ApiEndpoint` del stack (lo da
`sam list stack-outputs --stack-name portfolio-backend-dev`).

### 2. Build local

```bash
pnpm install
pnpm run build
```

### 3. Deploy a Cloudflare Pages

Cada app es un proyecto Pages separado. Configurado por Wrangler / API
token (ver `.claude/docs/cloudflare/`). En CI/CD el push a `main`
dispara el deploy.

### 4. Activar dashboard

URL: `https://the-full-stack.com/dashboard`
Credenciales:

- Usuario: `owner`
- Password: el valor `DASHBOARD_PASSWORD` generado en Setup 3

## Post-deploy checklist

- [ ] Stack `portfolio-backend-dev` en `CREATE_COMPLETE`
- [ ] 5 Lambdas en estado `Active`
- [ ] 5 tablas DynamoDB con `Status: ACTIVE`
- [ ] API GW retorna 200 al `OPTIONS /contact`
- [ ] Smoke test pasa (`scripts/smoke_test.sh dev`)
- [ ] Migrations aplicadas en Neon (5 migrations en `migrations_log`)
- [ ] Email de prueba llega al `owner-email`
- [ ] Dashboard accesible con basic auth
- [ ] AWS Billing Alarm creada
- [ ] Outputs actualizados en `docs/deployment-outputs-{dev,prod}.md`

## Troubleshooting comun

| Sintoma | Causa | Solucion |
|---------|-------|----------|
| `An error occurred (UnauthorizedOperation)` | SSO token expirado | `aws sso login --profile tfs-dev` |
| `ROLLBACK_COMPLETE` en stack | Recurso no creado en deploy previo | `aws cloudformation delete-stack ...` + re-deploy |
| `No module named 'common'` en Lambda | `CodeUri`/`Handler` mal | Ver `template.yaml`: `CodeUri: src/`, `Handler: contact_form.handler.lambda_handler` |
| `email-validator` import error | Layer no incluye `pydantic[email]` | Re-build layer con `pip install pydantic[email]` en `requirements.txt` |
| Smoke test 502 en `/contact` | Lambda timeout o env var missing | Tail logs: `sam logs -n ContactFormFunction --stack-name portfolio-backend-dev --tail` |
| Dashboard 500 en `/dashboard/summary` | Neon connection failed | Verificar `/portfolio/neon-url` apunta al branch correcto |

Mas casos en [RUNBOOK.md](RUNBOOK.md#troubleshooting).

## Decisiones del deploy

- **us-east-1** (no us-west-2): SES production access ya estaba GRANTED
  en us-east-1 para evitar 24-48h de espera adicional
- **arm64 Graviton2**: 20% mas barato + mismo perf en Python 3.13
- **CodeUri `src/`**: Lambdas comparten layer comun via `src/common/`
- **Sin AWS::CloudWatch::Alarm operacionales**: Solo billing alarm
  global. Logs son la fuente de verdad para troubleshooting (ver RUNBOOK)
- **Sin AWS WAF Web ACL**: Rate-limit self-managed con DynamoDB ahorra
  $7/mes (ver `.claude/docs/serverless-rate-limit/`)
