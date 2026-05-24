# Secrets del backend serverless — inventario y politicas

> Catalogo de secretos del backend serverless del portfolio: que es, donde
> vive, quien lo consume, como se rota. **Es la rule hija de la
> categoria `server`** de [secrets-strategy.md](secrets-strategy.md)
> (umbrella).
>
> **Fuente de verdad del inventario**:
> `serverless/lambda/resources/secrets/*.yaml` (catalogo declarativo,
> un YAML por entrada). devtools lo carga via
> `serverless.secrets_catalog.Catalog.load()`. Los diccionarios
> hardcodeados `_SECRETS` (provisioner.py) y `_SSM_PARAMETERS`
> (secrets.py) **fueron eliminados** — el catalogo YAML los reemplaza.
>
> **Comando recomendado para sync (unificado)**:
> `python devtools/run.py sync_secrets --env=<X> --category=server
> --aws-profile=tfs-dev`. El comando `serverless sync-secrets` sigue
> accesible para operar solo el server backend.

## Activacion

Aplica SIEMPRE que se trabaje con:

- Parametros SSM del portfolio (`/portfolio/*`)
- La KMS key `alias/portfolio-lambdas`
- Rotacion de secretos (Turnstile, Neon URL, emails)
- IAM scopes de las Lambdas del backend
- `devtools/serverless/secrets.py` (comandos `setup-ssm`, `sync-secrets`,
  `secrets-status`, `validate-catalog`, `rotate-secret`)
- Configuracion de AWS SES del portfolio
- `serverless/lambda/resources/secrets/*.yaml` (catalogo)

## Reglas criticas (SIEMPRE / NUNCA)

- **SIEMPRE** los secretos del backend se declaran en
  `serverless/lambda/resources/secrets/<short-name>.yaml`. Una entrada
  por secreto, schema documentado en
  `serverless/lambda/resources/secrets/README.md`.
- **SIEMPRE** `docker/env/server/.{stage}` es la fuente del VALOR.
  devtools (en `serverless deploy`) lee el .env y publica a SSM —
  hermetico, sin imprimir valores.
- **SIEMPRE** las Lambdas leen secretos via
  `shared.aws.ssm.get_secret_by_name(short_name, local_env=<KEY>)`. En
  cloud lee `SSM_<UPPER>_PATH`; en local lee `<source_env_var>` directo.
- **SIEMPRE** los secretos rotables (Turnstile secret, Neon URL) son
  `SecureString` cifrados con `alias/portfolio-lambdas`.
- **SIEMPRE** IAM least privilege: cada Lambda tiene `ssm:GetParameter`
  solo sobre los ARNs que necesita (ver tabla de scopes abajo).
- **NUNCA** hardcodear un secreto en codigo ni en `manifest.yaml`.
- **NUNCA** logear el valor de un `SecureString`.
- **NUNCA** publicar a `/portfolio/local/*` — local NO usa SSM
  (devtools inyecta env vars directo al runtime).
- **NUNCA** dejar un CloudWatch Log Group con `retention=Never`:
  el backend usa `LogRetentionInDays: 7`.

## Resumen ejecutivo

| Tipo de secreto | Donde vive | Quien lo lee | Rotacion |
|-----------------|------------|--------------|----------|
| Rotables (Turnstile, Neon) | SSM Parameter Store + KMS | Lambdas en runtime (boto3) | Manual via `serverless setup-ssm` |
| Constantes (emails, addresses) | SSM Parameter Store (plain String) | Lambdas en runtime (boto3) | Manual (raro) |
| Build-time vars (CORS, hostnames) | `manifest.yaml` del Lambda | Lambdas en runtime (env var) | Cambio en `manifest.yaml` + redeploy |
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
  `manifest.yaml` de la Lambda `db` declara `SSM_NEON_URL_PATH` como
  `/portfolio/${stage}/neon-url` y devtools la inyecta como env var
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
  hace `split(',')` + `strip()` y descarta vacios.
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
| `contact_form` | `turnstile-secret`, `owner-email`, `ses-from-address` + paths `dynamodb/{contacts,cache,rate-limit-*}` | Si (solo turnstile-secret) |
| `tracking_pixel` | paths `dynamodb/{tracking,cache,rate-limit-*}` | No |
| `stream_processor` | `neon-url` + paths `dynamodb/{contacts,tracking}` | Si |

Los paths `/portfolio/{stage}/dynamodb/...` son `String` planos (nombre/ARN
de recurso, no secreto); su lectura no requiere `kms:Decrypt`. Solo
`turnstile-secret` y `neon-url` son `SecureString`.

## SSM params de infraestructura — publicados al provisionar los recursos

Los recursos compartidos se declaran en
`serverless/lambda/resources/<tipo>/<nombre>.yaml` (esquema propio de
devtools, sin IaC declarativa). Al provisionarlos, devtools **publica**
sus identificadores en SSM Parameter Store, con el patron de path
`/portfolio/{stage}/{tipo}/{nombre}/{atributo}`. Son `String` planos (no
secretos): el nombre/ARN de un recurso AWS no es sensible. Asi cada
recurso se puede recrear sin bloquear a quien lo consume.

| Path SSM | Que publica |
|----------|-------------|
| `/portfolio/{stage}/dynamodb/contacts/{name,arn,stream-arn}` | tabla DynamoDB de contactos |
| `/portfolio/{stage}/dynamodb/tracking/{name,arn,stream-arn}` | tabla DynamoDB de tracking events |
| `/portfolio/{stage}/dynamodb/cache/{name,arn}` | tabla DynamoDB de cache |
| `/portfolio/{stage}/dynamodb/rate-limit-rules/{name,arn}` | tabla DynamoDB de reglas de rate-limit |
| `/portfolio/{stage}/dynamodb/rate-limit-buckets/{name,arn}` | tabla DynamoDB de buckets de rate-limit |
| `/portfolio/{stage}/api_gateway/portfolio-api/{id,root-resource-id,access-log-group-arn}` | API Gateway REST |
| `/portfolio/{stage}/sqs/stream-processor-dlq/{arn,url}` | DLQ del `stream_processor` |

Las Lambdas resuelven el **nombre de cada tabla DynamoDB en el cold start**
leyendo el path SSM correspondiente: devtools les inyecta una env var
`SSM_<TABLA>_TABLE_PATH` (ej. `SSM_CONTACTS_TABLE_PATH=/portfolio/dev/dynamodb/contacts/name`)
y el codigo hace `ssm:GetParameter` sobre ese path, en vez de recibir el
nombre directo en `CONTACTS_TABLE_NAME`. El Stream ARN, el DLQ ARN y el
`ApiId` los resuelve `provisioner.py` con `aws ssm get-parameter` al
momento del `deploy` (los necesita para crear el Event Source Mapping y
las rutas de la API), no en runtime del Lambda.

## Env vars constantes (sin SSM)

Se declaran en el `manifest.yaml` del Lambda (bloque `environment`) y
devtools las inyecta como env vars de la funcion. Son derivables;
cambiarlas implica redeploy.

| Variable | Donde se setea | Quien la usa |
|----------|----------------|--------------|
| `POWERTOOLS_SERVICE_NAME` / `POWERTOOLS_METRICS_NAMESPACE` | `manifest.yaml` del Lambda | Powertools |
| `LOG_LEVEL` | `manifest.yaml` del Lambda (INFO dev / WARNING prod) | logger |
| `CORS_ALLOWED_ORIGINS` | `manifest.yaml` del Lambda | `common.cors.resolve_origin` |
| `SSM_CONTACTS_TABLE_PATH` / `SSM_TRACKING_TABLE_PATH` / `SSM_CACHE_TABLE_PATH` | `manifest.yaml` del Lambda | persistence / cache (resuelven el nombre de tabla en cold start) |
| `SSM_RATE_LIMIT_RULES_TABLE_PATH` / `SSM_RATE_LIMIT_BUCKETS_TABLE_PATH` | `manifest.yaml` del Lambda | `common.rate_limit` |
| `AWS_SES_REGION` | `manifest.yaml` del `contact_form` | `notification.py` (SPEC-100) |

## Credenciales de deploy (no SSM)

Las credenciales que devtools usa para provisionar la infra con AWS CLI
NO viven en AWS:

- IAM user `dev` (grupo `Admin`, `AdministratorAccess`).
- Viven en `docker/env/dev-cli/.{dev,local,prod}` (gitignored, categoria
  `dev-cli` — ver [env-files.md](env-files.md): NUNCA leer el `.env`).
- Rotacion: cuando la key supera 90 dias o ante sospecha de leak — crear key
  nueva en IAM Console, deshabilitar la antigua 24h, actualizar el `.env`,
  borrar la antigua tras 24h sin uso.
- Alternativa SSO para uso manual: `aws sso login --profile tfs-dev`.

> **Perfil AWS de los comandos `serverless`.** El backend del portfolio vive
> en la cuenta `637423614564`, accesible con el perfil `tfs-dev`. Los
> comandos `deploy`, `destroy`, `status`, `provision-infra` y `run`
> (contra un stage provisionado) del script `serverless` aceptan
> `--aws-profile=tfs-dev` para fijar ese perfil en los comandos `aws`
> que ejecutan. Sin el flag usan el perfil del shell
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
| Secreto hardcodeado en el `manifest.yaml` | Expuesto en git | SSM `SecureString` + KMS |
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
