# RUNBOOK — Operacion del backend serverless

> Operaciones del dia a dia + troubleshooting. Para el primer deploy
> ver [DEPLOYMENT.md](DEPLOYMENT.md). Para diseno ver
> [ARCHITECTURE.md](ARCHITECTURE.md).

## Inventario de recursos

### Lambdas (3, region us-east-1)

| Funcion | Endpoint / Trigger | Memoria | Timeout |
|---------|-------------------|---------|---------|
| `ContactFormFunction` | `POST /contact` | 512 MB | 10s |
| `TrackingPixelFunction` | `POST /track` | 256 MB | 5s |
| `StreamProcessorFunction` | DynamoDB Streams (contacts, tracking) | 512 MB | 60s |

### DynamoDB (5 tablas x 2 stages)

- `portfolio-contacts-{dev,prod}` (Stream, TTL 60d)
- `portfolio-tracking-{dev,prod}` (Stream, TTL 60d)
- `portfolio-cache-{dev,prod}` (TTL variable)
- `portfolio-rate-limit-{dev,prod}` (TTL 1h)
- `portfolio-rate-limit-rules-{dev,prod}` (no TTL, manual)

### Externos

- Neon Postgres: branches `dev` y `prod`
- SES (us-east-1, production access GRANTED)
- Cloudflare Turnstile (1 widget para 6 hostnames)
- SSM Parameters bajo `/portfolio/*`
- KMS key `alias/portfolio-lambdas`

## Operaciones frecuentes

### Ver logs (tail)

```bash
# Cualquier funcion en tiempo real
sam logs -n ContactFormFunction --stack-name portfolio-backend-dev \
  --profile tfs-dev --tail

# Filtrar por nivel
sam logs -n StreamProcessorFunction --stack-name portfolio-backend-dev \
  --profile tfs-dev --filter "ERROR"

# Rango de tiempo
sam logs -n TrackingPixelFunction --stack-name portfolio-backend-dev \
  --profile tfs-dev --start-time '10min ago'
```

### Invocar Lambda manualmente

```bash
# Local (sin internet)
sam local invoke ContactFormFunction \
  --event events/contact_form_valid.json

# Remoto (stage real)
aws lambda invoke --profile tfs-dev --region us-east-1 \
  --function-name portfolio-backend-dev-StreamProcessorFunction \
  --payload '{}' /tmp/response.json
cat /tmp/response.json
```

### Rotar Turnstile secret

```bash
# 1. Generar nuevo secret en https://dash.cloudflare.com/.../turnstile
# 2. Actualizar SSM Parameter
aws ssm put-parameter --profile tfs-dev --region us-east-1 \
  --name /portfolio/turnstile-secret \
  --type SecureString --key-id alias/portfolio-lambdas \
  --value "<NEW_SECRET>" \
  --overwrite

# 3. Forzar refresh del cache de SSM (depende de implementacion)
#    Lambda lo lee on cold start. Para forzar:
#    Opcion A: redeploy sin cambios (sam deploy)
#    Opcion B: esperar al proximo cold start natural (~15min idle)

# 4. Smoke test
./scripts/smoke_test.sh dev
```

### Rotar Neon connection URL

```bash
# 1. Generar nueva credencial en Neon console -> Roles
# 2. Actualizar SSM (NUNCA modificar a mano si hay traffic)
aws ssm put-parameter --profile tfs-dev --region us-east-1 \
  --name /portfolio/neon-url \
  --type SecureString --key-id alias/portfolio-lambdas \
  --value "postgresql://user:newpass@host/db?sslmode=require" \
  --overwrite

# 3. Revocar credencial vieja en Neon console (despues de validar)
# 4. Smoke test pipeline E2E: POST /track -> verificar row en Neon
```

### Aplicar migrations Postgres sin downtime

```bash
# 1. Crear nueva migration (idempotente, no rompe schema existente)
#    Reglas: solo CREATE TABLE IF NOT EXISTS, ALTER ADD COLUMN, etc.
#    NUNCA DROP COLUMN ni ALTER TYPE en hot path

# 2. Aplicar contra dev primero
DATABASE_URL="<NEON_URL_DEV>" python scripts/migrate.py up

# 3. Verificar tracking_events sigue insertando OK
./scripts/smoke_test.sh dev

# 4. Aplicar a prod
DATABASE_URL="<NEON_URL_PROD>" python scripts/migrate.py up

# 5. Smoke test prod
./scripts/smoke_test.sh prod
```

### Manejar mensajes en DLQ (StreamProcessor)

```bash
# 1. Ver cantidad de mensajes
aws sqs get-queue-attributes --profile tfs-dev --region us-east-1 \
  --queue-url <DLQ_URL> \
  --attribute-names ApproximateNumberOfMessages

# 2. Peek primer mensaje
aws sqs receive-message --profile tfs-dev --region us-east-1 \
  --queue-url <DLQ_URL> \
  --max-number-of-messages 1 \
  --visibility-timeout 30 | jq .

# 3. Diagnosticar (typo en schema? Neon down? bug en transformer?)
#    Logs de StreamProcessor en el rango del mensaje

# 4. Una vez fixed el bug, reprocesar
aws sqs send-message --profile tfs-dev --region us-east-1 \
  --queue-url <STREAM_INPUT_REDRIVE> --message-body '<original>'

# 5. Purge si los mensajes son ya viejos / irrecuperables
aws sqs purge-queue --profile tfs-dev --region us-east-1 \
  --queue-url <DLQ_URL>
```

### Agregar regla de rate-limit

Las reglas viven en `portfolio-rate-limit-rules-{stage}`. Schema:

```text
pk:   RULE#<scope>
sk:   #META
type: ip_blacklist | ip_whitelist | country_block | path_limit
config: JSON-encoded
```

Ejemplo: blacklist IP `192.0.2.1` por 7 dias:

```bash
aws dynamodb put-item --profile tfs-dev --region us-east-1 \
  --table-name portfolio-rate-limit-rules-dev \
  --item '{
    "pk": {"S": "RULE#blacklist#192.0.2.1"},
    "sk": {"S": "#META"},
    "type": {"S": "ip_blacklist"},
    "config": {"S": "{\"reason\":\"manual_block\",\"expires_at\":1734567890}"},
    "ttl": {"N": "1734567890"}
  }'
```

Quitar regla:

```bash
aws dynamodb delete-item --profile tfs-dev --region us-east-1 \
  --table-name portfolio-rate-limit-rules-dev \
  --key '{"pk":{"S":"RULE#blacklist#192.0.2.1"},"sk":{"S":"#META"}}'
```

### Invalidar cache (tag global)

```bash
# Por key especifica
aws dynamodb delete-item --profile tfs-dev --region us-east-1 \
  --table-name portfolio-cache-dev \
  --key '{"cache_key":{"S":"<key>"}}'

# Por tag (requiere scan + batch delete; ver src/common/cache/invalidation.py)
python scripts/cache_invalidate.py --stage dev --tag user:abc123
```

### Re-deploy de una sola Lambda

```bash
# SAM no soporta deploy de funciones individuales,
# pero podes actualizar el codigo sin redeploy del stack
sam build ContactFormFunction
aws lambda update-function-code --profile tfs-dev --region us-east-1 \
  --function-name portfolio-backend-dev-ContactFormFunction \
  --zip-file fileb://.aws-sam/build/ContactFormFunction.zip
```

Para cambios de IAM / config / Events: requiere `sam deploy` completo.

## Verificacion de alarmas

```bash
# Listar alarmas (esperado: 0 operacionales)
aws cloudwatch describe-alarms --profile tfs-dev --region us-east-1 \
  --alarm-name-prefix portfolio- \
  --query 'MetricAlarms[].[AlarmName,StateValue]' --output table

# Billing alarm global (us-east-1 obligatorio para AWS/Billing)
aws cloudwatch describe-alarms --profile tfs-dev --region us-east-1 \
  --alarm-names portfolio-billing-alarm
```

## Troubleshooting

### Smoke test falla en `OPTIONS /contact`

- Revisar CORS en `template.yaml` -> `Cors:` block
- `Access-Control-Allow-Origin` debe incluir el dominio que envia
- API GW deploy lag: esperar 30s tras `sam deploy`

### `502 Bad Gateway` intermitente

- Probable cold start con Neon connection
- Verificar `provisioned_concurrency` no es necesario (cost: prefer
  warm-up con CloudWatch Events cada 5min si critico)
- Logs: buscar `psycopg.OperationalError: timeout`

### `POST /track` responde `400 INVALID_INPUT`

- El body de `/track` exige `event_type_id` (UUID del catalogo
  `event_types`, FK) y `event_id` (UUID del evento). Un body sin
  `event_type_id` o con un UUID malformado falla la validacion Pydantic
  de `TrackingEventInput` y la Lambda responde `400 INVALID_INPUT`.
- Verificar que el frontend (`TrackingPixel.astro`, ver SPEC-102) envia
  ambos campos: `event_id` como UUIDv4 por evento y `event_type_id` con
  el UUID de `page_load` del modulo de constantes de `@portfolio/content`.
- Confirmar el contrato del body con `src/tracking_pixel/schemas.py`.

### DLQ recibe mensajes constantes

- Probable schema mismatch despues de migration
- Revisar `transformers.py` vs migration SQL nueva
- Re-procesar despues de fix con script de redrive

### Email no llega (form contact)

```bash
# 1. SES sending stats
aws sesv2 get-account --profile tfs-dev --region us-east-1 \
  --query 'SendingEnabled, ProductionAccessEnabled'

# 2. Domain identity verificada
aws sesv2 get-email-identity --profile tfs-dev --region us-east-1 \
  --email-identity <dominio> \
  --query 'VerificationStatus'

# 3. Suppression list
aws sesv2 list-suppressed-destinations --profile tfs-dev --region us-east-1

# 4. Logs de Lambda ContactFormFunction (buscar "SES SendEmail")
```

### Costos suben sobre USD 5/mes

- Revisar AWS Cost Explorer por servicio
- DynamoDB: probable hot key, revisar metrics `ConsumedReadCapacityUnits`
- Lambda: revisar `Invocations` por funcion, posible bucle
- SES: verificar bounce rate < 5%
- Si llega DDoS L7: considerar reactivar AWS WAF Web ACL temporal
  (~$7/mes flat) hasta mitigar

### Ataque DDoS sostenido

1. Confirmar via la consola de API Gateway (`Count` metric explota)
2. Identificar IPs origen via `tracking_events.ip` en Neon
3. Bloquear IPs en `portfolio-rate-limit-rules-{stage}` (ver
   "Agregar regla de rate-limit")
4. Si bot pool grande, activar AWS WAF temporal:
   ```bash
   # Crear Web ACL minima + asociar API GW
   # (no esta IaC porque es opcional/temporal)
   ```
5. Si Cloudflare cubre el frontend, activar "Under Attack Mode" en
   la consola de Cloudflare (5 segundos challenge)
6. Logear el incidente con cantidad de IPs + ventana de tiempo

## Cuando escalar

- **Cloudflare support**: DDoS L7 con bot pool > 10k IPs / min
- **AWS support (Business plan)**: SES bounce rate > 10% sostenido
- **Neon support**: queries del stream_processor tardan > 60s sostenido

## Decisiones operacionales

- **0 AWS::CloudWatch::Alarm operacionales** — logs son la fuente
  de verdad. Filtros de log + consultas manuales con CW Logs Insights
- **Billing alarm como unica alarma** — la mas barata y la unica que
  importa para un portfolio personal sin SLA
- **Sin PagerDuty/Opsgenie** — proyecto personal, no hay on-call
- **Outputs en `docs/deployment-outputs-{dev,prod}.md`** — regenerar
  con `sam list stack-outputs --stack-name portfolio-backend-<stage>`
  tras cada deploy
