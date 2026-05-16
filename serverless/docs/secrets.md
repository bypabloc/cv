# Secrets - inventario y politicas

> Catalogo de secretos del backend serverless: que es, donde vive, quien lo
> consume, como se rota. Politica hibrida: SSM SecureString + KMS solo para
> los rotables; env vars planos para constantes derivables.

## Resumen ejecutivo

| Tipo de secreto | Donde vive | Quien lo lee | Rotacion |
|-----------------|-----------|--------------|----------|
| Rotables (Turnstile, Neon) | SSM Parameter Store + KMS | Lambdas en runtime (boto3) | Manual via `serverless setup-ssm` |
| Constantes (emails, addresses) | SSM Parameter Store (plain String) | Lambdas en runtime (boto3) | Manual (raro) |
| Build-time vars (CORS, hostnames) | SAM template Globals | Lambdas en runtime (env var) | Cambio en `template.yaml` + redeploy |
| AWS auth (deploy) | `docker/env/dev-cli/.{dev,local,prod}` (gitignored) | devtools en local | Manual cuando expira IAM key |

## SSM Parameter Store - inventario completo

### `/portfolio/turnstile-secret` (SecureString + KMS)

- **Que es**: Secret key del widget Cloudflare Turnstile `Portfolio Backend`
  (sitekey publica `0x4AAAAAADPSoiQA_-LcRafo`).
- **Quien lo lee**: Lambda `contact_form` para validar tokens contra
  `https://challenges.cloudflare.com/turnstile/v0/siteverify`. Tambien
  Lambda `turnstile_validator` (SPEC-007).
- **Hostnames cubiertos**: `the-full-stack.com`, `hub/fintech/architect/leader/vibe.portfolio.the-full-stack.com`,
  `localhost`, `127.0.0.1`.
- **Rotacion**: cuando el widget Turnstile se regenera en Cloudflare dashboard
  (o cuando se sospecha leak). Comando:

  ```bash
  # 1. Crear nuevo widget en CF dashboard o via API
  # 2. Actualizar SSM:
  python devtools/run.py serverless setup-ssm \
    --name=/portfolio/turnstile-secret \
    --key-id=alias/portfolio-lambdas --env=dev
  # 3. Actualizar TURNSTILE_SITE_KEY en docker/env/client/.{dev,local,prod}
  #    y TURNSTILE_SECRET_KEY en docker/env/server/.{dev,local,prod}
  # 4. Redeploy frontend para nuevo sitekey publico
  ```

- **IAM scope**: solo Lambdas `contact_form` y `turnstile_validator`
  tienen `ssm:GetParameter` sobre este ARN especifico.

### `/portfolio/neon-url` (SecureString + KMS)

- **Que es**: Connection string PostgreSQL del proyecto Neon
  (`postgresql://neondb_owner:***@ep-***.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require`).
- **Quien lo lee**: Lambdas `stream_processor` y `aggregator` (SPEC-009 + SPEC-010).
- **Rotacion**: cuando se rota el password del usuario `neondb_owner` en
  Neon Console > Roles. Comando:

  ```bash
  # 1. En Neon Console: rotar password de neondb_owner
  # 2. Copiar nuevo DB_URL
  # 3. Actualizar SSM:
  python devtools/run.py serverless setup-ssm \
    --name=/portfolio/neon-url \
    --key-id=alias/portfolio-lambdas --env=dev
  # 4. Actualizar DB_URL en docker/env/server/.{dev,local,prod}
  ```

- **IAM scope**: solo Lambdas `stream_processor` y `aggregator` tienen
  acceso a este ARN.

### `/portfolio/owner-email` (String)

- **Que es**: Email del owner del portfolio (destinatario del form de contacto).
- **Valor actual**: `pacg1991@gmail.com`
- **Quien lo lee**: Lambda `contact_form` para `SendEmail.Destination.ToAddresses`.
- **Rotacion**: cuando cambia el owner (raro). Comando:

  ```bash
  aws ssm put-parameter --name /portfolio/owner-email \
    --value "nuevo@email.com" --type String --overwrite --region us-east-1
  ```

### `/portfolio/ses-from-address` (String)

- **Que es**: Direccion remitente verificada en AWS SES para emails transaccionales.
- **Valor actual**: `no-reply@the-full-stack.com`
- **Quien lo lee**: Lambda `contact_form` para `SendEmail.FromEmailAddress`.
- **Rotacion**: solo si se cambia el domain o el alias. Requiere
  re-verificar la nueva address en SES.

### `/portfolio/dashboard-password-hash` (SecureString + KMS) - SPEC-014

- **Que es**: Hash bcrypt del password de acceso al dashboard analytics.
- **Quien lo lee**: Lambda `dashboard_api` (SPEC-014) para validar basic auth.
- **Rotacion**: manual cuando se rota el password del owner. Comando:

  ```bash
  # 1. Generar nuevo hash:
  python -c "import bcrypt; print(bcrypt.hashpw(b'NUEVO_PASS', bcrypt.gensalt()).decode())"
  # 2. Cargar a SSM:
  python devtools/run.py serverless setup-ssm \
    --name=/portfolio/dashboard-password-hash \
    --key-id=alias/portfolio-lambdas
  ```

## KMS key

### `alias/portfolio-lambdas`

- **Tipo**: Customer-managed symmetric key (no AWS-owned).
- **Region**: `us-east-1`.
- **Account**: `637423614564`.
- **Key ID actual**: `4325fc3d-429e-44ef-97f7-5685bf4fd2df`
- **Uso**: `ENCRYPT_DECRYPT` para SSM SecureStrings.
- **Rotacion automatica**: habilitada (anual).
- **Costo**: $1 USD/mes (unico AWS managed cost no-free-tier que aceptamos).
- **IAM scope**: cada Lambda que lee un SSM SecureString tiene `kms:Decrypt`
  scoped a este key ARN.

### Rotacion manual de la KMS key (si fuera necesario)

Solo cuando hay sospecha de compromiso. Procedimiento:

```bash
# 1. Crear nueva key
NEW_KEY_ID=$(aws kms create-key --description "Portfolio rotacion YYYY-MM-DD" \
  --region us-east-1 --query 'KeyMetadata.KeyId' --output text)

# 2. Apuntar alias a la nueva key
aws kms update-alias --alias-name alias/portfolio-lambdas \
  --target-key-id "$NEW_KEY_ID" --region us-east-1

# 3. Re-cifrar todos los SSM SecureStrings (cada parameter usando el nuevo KMS)
for p in turnstile-secret neon-url dashboard-password-hash; do
  current=$(aws ssm get-parameter --name "/portfolio/$p" \
    --with-decryption --region us-east-1 --query 'Parameter.Value' --output text)
  aws ssm put-parameter --name "/portfolio/$p" \
    --value "$current" --type SecureString \
    --key-id alias/portfolio-lambdas --overwrite --region us-east-1
done

# 4. Schedular eliminacion de la key antigua (min 7 dias)
aws kms schedule-key-deletion --key-id <KEY_ID_ANTIGUO> \
  --pending-window-in-days 30 --region us-east-1
```

## Env vars constantes (sin SSM)

Las siguientes constantes se inyectan al template SAM directamente (Lambda
`Environment` block), no via SSM. Son derivables y cambiar implica redeploy.

| Variable | Donde se setea | Quien la usa |
|----------|---------------|--------------|
| `POWERTOOLS_SERVICE_NAME` | `template.yaml` Globals | Powertools logger/tracer/metrics |
| `POWERTOOLS_METRICS_NAMESPACE` | `template.yaml` Globals | Powertools metrics |
| `LOG_LEVEL` | `template.yaml` Globals (per-stage: INFO dev / WARNING prod) | logger |
| `CORS_ALLOWED_ORIGINS` | `template.yaml` Globals | `common.cors.resolve_origin` |
| `CONTACTS_TABLE_NAME` | `template.yaml` Globals | persistence layer |
| `TRACKING_TABLE_NAME` | `template.yaml` Globals | persistence layer |
| `CACHE_TABLE_NAME` | `template.yaml` Globals | `common.cache` |
| `RATE_LIMIT_RULES_TABLE_NAME` | `template.yaml` Globals | `common.rate_limit.rules` |
| `RATE_LIMIT_BUCKETS_TABLE_NAME` | `template.yaml` Globals | `common.rate_limit.buckets` |

## Credenciales de deploy (no SSM)

Las credenciales que devtools usa para sam deploy NO viven en AWS — son
credenciales del IAM user `dev` en la categoria `dev-cli`:
`docker/env/dev-cli/.dev` (gitignored).

### `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`

- **IAM user**: `dev` en account `637423614564`.
- **Permisos**: grupo `Admin` con policy `AdministratorAccess` attached.
- **Donde vive**: `docker/env/dev-cli/.{dev,local,prod}` (gitignored,
  categoria `dev-cli`).
- **Rotacion**: cuando IAM detecta key activa > 90 dias (politica AWS) o
  cuando sospecha leak. Comando:

  ```bash
  # 1. AWS Console > IAM > Users > dev > Security credentials > Create access key
  # 2. Disable la key antigua (no delete inmediato; mantener 24h para detectar usos)
  # 3. Actualizar docker/env/dev-cli/.{dev,local,prod}
  # 4. Despues de 24h sin uso, delete la antigua
  ```

### Alternativa SSO: `tfs-dev`

Para uso manual (no devtools automatizado), usar SSO:

```bash
aws sso login --profile tfs-dev
# Token valido ~8-12h, refresh automatico
aws sts get-caller-identity --profile tfs-dev
```

## Tabla de IAM scopes por Lambda

Cada Lambda solo lee los parameters que necesita (least privilege).

| Lambda | SSM parameters | KMS Decrypt |
|--------|---------------|-------------|
| `contact_form` | `/portfolio/turnstile-secret`, `/portfolio/owner-email`, `/portfolio/ses-from-address` | Si (solo turnstile-secret) |
| `tracking_pixel` | ninguno | No |
| `turnstile_validator` | `/portfolio/turnstile-secret` | Si |
| `stream_processor` | `/portfolio/neon-url` | Si |
| `aggregator` | `/portfolio/neon-url` | Si |
| `dashboard_api` (SPEC-014) | `/portfolio/neon-url`, `/portfolio/dashboard-password-hash` | Si (ambos) |

## Politica de retencion CloudWatch Logs

Decision: `LogRetentionInDays: 7` para TODOS los CloudWatch Log Groups del
backend (Lambdas, API Gateway access logs, SES bounce notifications).

Razon:

- 7 dias cabe holgadamente en el free tier 5 GB/mes
- Suficiente para debuggear incidentes inmediatos
- Para auditoria > 7 dias: setear S3 export con lifecycle policy

**NUNCA** dejar log groups con `retention=Never` (default AWS) — explota el
costo en CloudWatch Logs sin valor.

## Lo que NO esta en SSM

Decision explicita de NO usar SSM para:

- `EMAIL_FROM` y `OWNER_EMAIL` planos: SI estan en SSM porque las Lambdas
  los leen en runtime (la decision arriba).
- `CORS_ALLOWED_ORIGINS`: en `template.yaml` Globals porque cambia con cada
  redeploy igual.
- `AWS_ACCESS_KEY_ID` del IAM user dev: NO en SSM (seria circular —
  necesitarias permisos para leer SSM antes de poder leer SSM).
- `CLOUDFLARE_API_TOKEN`: no se necesita en runtime de Lambdas (solo
  devtools en local lo usa).

## Auditoria de uso

Para revisar quien leyo cada parameter:

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=GetParameter \
  --region us-east-1 --max-results 50 \
  --query 'Events[*].[EventTime,Username,Resources[?ResourceType==`AWS::SSM::Parameter`].ResourceName | [0]]' \
  --output table
```

(CloudTrail registra la lectura solo de SecureString — String no se
audita por default).
