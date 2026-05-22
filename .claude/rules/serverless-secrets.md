# Secrets del backend serverless — inventario y politicas

> Catalogo de secretos del backend serverless del portfolio: que es, donde
> vive, quien lo consume, como se rota. Politica hibrida: SSM SecureString +
> KMS solo para los rotables; env vars planos para constantes derivables.
> Incluye el estado actual de AWS SES.

## Activacion

Aplica SIEMPRE que se trabaje con:

- Parametros SSM del portfolio (`/portfolio/*`)
- La KMS key `alias/portfolio-lambdas`
- Rotacion de secretos (Turnstile, Neon URL, emails)
- IAM scopes de las Lambdas del backend
- `devtools/serverless/secrets.py` (comando `serverless setup-ssm`)
- Configuracion de AWS SES del portfolio

## Reglas criticas (SIEMPRE / NUNCA)

- **SIEMPRE** los secretos rotables (Turnstile secret, Neon URL) viven en SSM
  Parameter Store como `SecureString` cifrado con la KMS key del proyecto.
- **SIEMPRE** las Lambdas leen los secretos en runtime via `boto3`, NUNCA
  como env var plano del template.
- **SIEMPRE** IAM least privilege: cada Lambda tiene `ssm:GetParameter` solo
  sobre los ARNs que necesita (ver tabla de scopes abajo).
- **NUNCA** hardcodear un secreto en codigo, `template.yaml`, `samconfig.toml`
  ni en archivos `.env` commiteados.
- **NUNCA** logear el valor de un `SecureString` (Turnstile secret, Neon URL).
- **NUNCA** dejar un CloudWatch Log Group con `retention=Never` (default AWS):
  el backend usa `LogRetentionInDays: 7` en todos.
- El inventario `_SSM_PARAMETERS` en `devtools/serverless/secrets.py` debe
  mantenerse sincronizado con este documento.

## Resumen ejecutivo

| Tipo de secreto | Donde vive | Quien lo lee | Rotacion |
|-----------------|------------|--------------|----------|
| Rotables (Turnstile, Neon) | SSM Parameter Store + KMS | Lambdas en runtime (boto3) | Manual via `serverless setup-ssm` |
| Constantes (emails, addresses) | SSM Parameter Store (plain String) | Lambdas en runtime (boto3) | Manual (raro) |
| Build-time vars (CORS, hostnames) | SAM template Globals | Lambdas en runtime (env var) | Cambio en `template.yaml` + redeploy |
| AWS auth (deploy) | `docker/env/dev-cli/.{dev,local,prod}` (gitignored) | devtools en local | Manual cuando expira IAM key |

## SSM Parameter Store — inventario completo

### `/portfolio/turnstile-secret` (SecureString + KMS)

- **Que es**: secret key del widget Cloudflare Turnstile `Portfolio Backend`
  (sitekey publica `0x4AAAAAADPSoiQA_-LcRafo`).
- **Quien lo lee**: Lambda `contact_form` (via `common/turnstile.py`) para
  validar tokens contra `challenges.cloudflare.com/turnstile/v0/siteverify`.
- **Hostnames cubiertos**: `the-full-stack.com`,
  `{hub,fintech,architect,leader,vibe}.portfolio.the-full-stack.com`,
  `localhost`, `127.0.0.1`.
- **Rotacion**: cuando el widget Turnstile se regenera en Cloudflare (o ante
  sospecha de leak):

  ```bash
  python devtools/run.py serverless setup-ssm \
    --name=/portfolio/turnstile-secret \
    --key-id=alias/portfolio-lambdas --env=dev
  # luego actualizar TURNSTILE_SITE_KEY en docker/env/client/.{dev,local,prod}
  # y TURNSTILE_SECRET_KEY en docker/env/server/.{dev,local,prod}
  # y redeploy del frontend para el nuevo sitekey publico
  ```

### `/portfolio/{stage}/neon-url` (SecureString + KMS)

- **Que es**: connection string PostgreSQL del proyecto Neon (pooled,
  `sslmode=require`), una por stage para aislamiento dev/prod a nivel DB.
- **Parametros**: `/portfolio/dev/neon-url` y `/portfolio/prod/neon-url`. El
  `template.yaml` resuelve `SSM_NEON_URL_PATH: !Sub /portfolio/${Stage}/neon-url`
  (SPEC-202, Fase 2). El `/portfolio/neon-url` plano queda como legacy/fallback.
- **Quien lo lee**: Lambda `stream_processor`.
- **Rotacion**: cuando se rota el password de `neondb_owner` en Neon Console:

  ```bash
  python devtools/run.py serverless setup-ssm \
    --name=/portfolio/dev/neon-url \
    --key-id=alias/portfolio-lambdas --env=dev
  # luego actualizar DB_URL en docker/env/server/.{dev,local,prod}
  ```

> Pendiente operativo: `/portfolio/dev/neon-url` y `/portfolio/prod/neon-url`
> se crearon en Fase 2 copiando el valor del `/portfolio/neon-url` legacy (que
> apunta al branch Neon `production`). Para aislamiento real, rotar
> `/portfolio/dev/neon-url` a la connection string del branch Neon `dev`.

  Detalle operativo de Neon: ver [neon-management.md](neon-management.md).

### `/portfolio/owner-email` (String)

- **Que es**: email(s) del owner, destinatario(s) del form de contacto.
- **Quien lo lee**: Lambda `contact_form` para `SendEmail.Destination.ToAddresses`.
- **Formato**: una o varias direcciones separadas por coma. `notification.py`
  hace `split(',')` + `strip()` y descarta vacios (ver SPEC-100 en
  `docs/specs/tracking-and-ses/`).
- **Rotacion**: cuando cambian los destinatarios:

  ```bash
  aws ssm put-parameter --name /portfolio/owner-email \
    --value "a@x.com,b@y.com" --type String --overwrite --region us-east-1
  ```

### `/portfolio/ses-from-address` (String)

- **Que es**: direccion remitente verificada en SES para emails transaccionales.
- **Valor**: `no-reply@the-full-stack.com`.
- **Quien lo lee**: Lambda `contact_form` para `SendEmail.FromEmailAddress`.
- **Rotacion**: solo si cambia el domain o alias; requiere re-verificar la
  nueva address en SES.

## KMS key — `alias/portfolio-lambdas`

- **Tipo**: customer-managed symmetric key (`ENCRYPT_DECRYPT`).
- **Region**: `us-east-1`.
- **Uso**: cifrado de los SSM `SecureString`.
- **Rotacion automatica**: habilitada (anual).
- **Costo**: ~$1 USD/mes (unico costo AWS no-free-tier aceptado).
- **IAM scope**: cada Lambda que lee un `SecureString` tiene `kms:Decrypt`
  scoped al ARN de esta key.

> El Key ID y el AWS Account ID son datos de infraestructura; resolverlos en
> runtime con `aws kms describe-key --key-id alias/portfolio-lambdas` y
> `aws sts get-caller-identity`. NO hardcodearlos en codigo.

### Rotacion manual de la KMS key (solo ante compromiso)

```bash
NEW_KEY_ID=$(aws kms create-key --description "Portfolio rotacion YYYY-MM-DD" \
  --region us-east-1 --query 'KeyMetadata.KeyId' --output text)
aws kms update-alias --alias-name alias/portfolio-lambdas \
  --target-key-id "$NEW_KEY_ID" --region us-east-1
# re-cifrar cada SecureString con la nueva key:
for p in turnstile-secret neon-url; do
  current=$(aws ssm get-parameter --name "/portfolio/$p" \
    --with-decryption --region us-east-1 --query 'Parameter.Value' --output text)
  aws ssm put-parameter --name "/portfolio/$p" --value "$current" \
    --type SecureString --key-id alias/portfolio-lambdas \
    --overwrite --region us-east-1
done
# schedular eliminacion de la key antigua (min 7 dias)
aws kms schedule-key-deletion --key-id <KEY_ID_ANTIGUO> \
  --pending-window-in-days 30 --region us-east-1
```

## IAM scopes por Lambda (least privilege)

| Lambda | SSM parameters | KMS Decrypt |
|--------|----------------|-------------|
| `contact_form` | `turnstile-secret`, `owner-email`, `ses-from-address` | Si (solo turnstile-secret) |
| `tracking_pixel` | ninguno | No |
| `stream_processor` | `neon-url` | Si |

## Env vars constantes (sin SSM)

Se inyectan al template SAM (bloque `Environment` de la Lambda), no via SSM.
Son derivables; cambiarlas implica redeploy.

| Variable | Donde se setea | Quien la usa |
|----------|----------------|--------------|
| `POWERTOOLS_SERVICE_NAME` / `POWERTOOLS_METRICS_NAMESPACE` | `template.yaml` Globals | Powertools |
| `LOG_LEVEL` | `template.yaml` Globals (INFO dev / WARNING prod) | logger |
| `CORS_ALLOWED_ORIGINS` | `template.yaml` Globals | `common.cors.resolve_origin` |
| `CONTACTS_TABLE_NAME` / `TRACKING_TABLE_NAME` / `CACHE_TABLE_NAME` | `template.yaml` Globals | persistence / cache |
| `RATE_LIMIT_RULES_TABLE_NAME` / `RATE_LIMIT_BUCKETS_TABLE_NAME` | `template.yaml` Globals | `common.rate_limit` |
| `AWS_SES_REGION` | `template.yaml` (`ContactFormFunction`) | `notification.py` (SPEC-100) |

## Credenciales de deploy (no SSM)

Las credenciales que devtools usa para `sam deploy` NO viven en AWS:

- IAM user `dev` (grupo `Admin`, `AdministratorAccess`).
- Viven en `docker/env/dev-cli/.{dev,local,prod}` (gitignored, categoria
  `dev-cli` — ver [env-files.md](env-files.md): NUNCA leer el `.env`).
- Rotacion: cuando la key supera 90 dias o ante sospecha de leak — crear key
  nueva en IAM Console, deshabilitar la antigua 24h, actualizar el `.env`,
  borrar la antigua tras 24h sin uso.
- Alternativa SSO para uso manual: `aws sso login --profile tfs-dev`.

> **Perfil AWS de los comandos `serverless`.** El backend del portfolio vive
> en la cuenta `637423614564`, accesible con el perfil `tfs-dev`. Los
> comandos `deploy`, `deploy-infra` e `invoke-remote` del script
> `serverless` aceptan `--aws-profile=tfs-dev` para fijar ese perfil en los
> comandos `aws`/`sam` que ejecutan. Sin el flag usan el perfil del shell
> (`AWS_PROFILE`/`[default]`), que puede apuntar a otra cuenta o tener el
> token SSO expirado — sintoma: `Error when retrieving token from sso` aun
> tras `aws sso login`. SIEMPRE pasar `--aws-profile=tfs-dev` o
> `export AWS_PROFILE=tfs-dev` en la sesion de trabajo del portfolio.

`CLOUDFLARE_API_TOKEN` no se necesita en runtime de las Lambdas; solo lo usa
devtools en local.

## AWS SES — estado actual

| Item | Valor |
|------|-------|
| Region | `us-east-1` |
| Domain identity | `the-full-stack.com` — Verified |
| Production access | GRANTED (fuera de sandbox) |
| Daily quota | 50,000 emails/dia |
| Send rate | 14 emails/seg |
| Mail type | TRANSACTIONAL |
| Suppression list | BOUNCE + COMPLAINT auto-gestionada |

- **DKIM**: 3 CNAMEs autogenerados por SES, configurados en Cloudflare DNS
  para `the-full-stack.com`.
- **SPF**: TXT `v=spf1 include:amazonses.com -all` en Cloudflare DNS.
- **DMARC**: TXT `v=DMARC1; p=quarantine; rua=mailto:...` en Cloudflare DNS.

Verificacion idempotente:

```bash
aws sesv2 list-email-identities --region us-east-1 \
  --query 'EmailIdentities[*].[IdentityName,VerificationStatus,SendingEnabled]'
aws sesv2 get-account --region us-east-1 \
  --query 'SendQuota.[Max24HourSend,MaxSendRate,SentLast24Hours]'
aws sesv2 get-email-identity --email-identity the-full-stack.com \
  --region us-east-1 --query 'DkimAttributes'
```

Detalle de SES (v2 API, MJML, bounce/complaint): skill `aws-ses`.

## Auditoria de uso

CloudTrail registra la lectura de `SecureString` (no de `String`):

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=GetParameter \
  --region us-east-1 --max-results 50 \
  --query 'Events[*].[EventTime,Username]' --output table
```

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Secreto hardcodeado en `template.yaml` | Expuesto en git | SSM `SecureString` + KMS |
| Lambda lee el secreto como env var plano | El valor queda en la config de la Lambda | Leer de SSM en runtime con boto3 |
| `ssm:GetParameter` con wildcard `/portfolio/*` | Rompe least privilege | ARN especifico por Lambda |
| Logear la Neon URL o el Turnstile secret | Leak en CloudWatch | Referir al nombre del parametro, nunca al valor |
| Key ID / Account ID hardcodeados | Frágil ante rotacion | Resolver con `aws kms describe-key` / `sts get-caller-identity` |
| Log Group con `retention=Never` | Costo CloudWatch sin tope | `LogRetentionInDays: 7` |

## Referencias cruzadas

- [neon-management.md](neon-management.md) — operacion de Neon (la URL es un
  secreto de esta rule; la gestion de migrations/branches vive alla)
- [env-files.md](env-files.md) — NUNCA leer `.env`; extraer keys puntuales
- [security.md](security.md) — politica general de secretos del repo
- skill `aws-ses` — SES v2, DKIM/SPF/DMARC, deliverability, bounce/complaint
- skill `cloudflare-turnstile` — el widget cuyo secret vive en SSM
- `docs/specs/tracking-and-ses/SPEC-100-ses-funcional.md` — uso de
  `owner-email` y `ses-from-address` en el form de contacto
