# Verificacion E2E iterativa (fase final, gate del PR)

> Bateria de verificacion completa. NO se mergea el PR hasta que esta
> bateria pase verde en dev, stage y prod. Es la ultima fase. El ultimo
> commit del PR (`test(e2e): verificacion direct-to-neon ...`) incluye
> el `git rm -r docs/specs/direct-neon-writes/`.

[Volver al README](README.md)

## Parte A — refactor de tests (cero referencias huerfanas)

```bash
# Ningun test viejo de stream_processor sobrevive:
test ! -d serverless/lambda/services/stream_processor/tests && echo "OK"

# rg busca cualquier referencia residual:
rg -l 'stream_processor|ProcessedStreamEvent|is_event_processed|mark_event_processed|_wire_table_changes_trigger' \
  serverless/ devtools/ packages/ apps/ \
  --glob '!docs/specs/direct-neon-writes/**'
# Debe retornar: nada

# Tests nuevos en ruta correcta:
ls serverless/lambda/services/tracking_pixel/tests/unit/test_tracking_service_persists_to_neon.py
ls serverless/lambda/services/contact_form/tests/unit/test_contact_service_persists_to_neon.py
```

## Parte B — bateria de comandos reales (no parar hasta verde)

### B.1 Local (verde antes de push)

```bash
# Bateria del backend serverless
python devtools/run.py serverless tests --type=unit --lambda=tracking_pixel
python devtools/run.py serverless tests --type=unit --lambda=contact_form
python devtools/run.py serverless tests --type=unit --lambda=db
python devtools/run.py serverless tests --type=integration --lambda=tracking_pixel
python devtools/run.py serverless tests --type=integration --lambda=contact_form

# Devtools tests
python devtools/run.py test_runner --module=devtools --type=unit

# Lint
pnpm exec biome check .
```

### B.2 dev (tras merge a feature branch, CI deploys o yo deployo)

```bash
# 1. Migration en Neon dev
python devtools/run.py serverless run --stage=dev --lambda=db \
  --event=events/migrate.json --aws-profile=tfs-dev
python devtools/run.py serverless run --stage=dev --lambda=db \
  --event=events/current.json --aws-profile=tfs-dev
# -> Verifica que la rev de drop_processed_stream_events esta aplicada

# 2. Deploy los 2 lambdas
python devtools/run.py serverless deploy --lambda=tracking_pixel --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless deploy --lambda=contact_form --stage=dev --aws-profile=tfs-dev

# 3. Verificar /track end-to-end
curl -X POST https://api.portfolio.dev.the-full-stack.com/track \
  -H "Content-Type: application/json" \
  -d '{
    "operation":"track","action":"create",
    "session_id":"019e5b00-0000-7000-8000-000000000001",
    "event_id":"019e5b00-0000-7001-8000-000000000001",
    "event_type_id":"019e372b-e0a7-7154-8279-8829bcf6a08c",
    "page_url":"https://portfolio.dev.the-full-stack.com/verify",
    "page_path":"/verify","page_title":"Verify",
    "niche":"generic","viewport_width":1920,"viewport_height":1080
  }'

# 4. Confirmar fila en Neon
python devtools/run.py serverless run --stage=dev --lambda=db \
  --event=events/tables.json --aws-profile=tfs-dev | grep -A2 tracking_events_default
# -> rows debe haber incrementado

# 5. Verificar /contact (con Turnstile bypass-secret en dev)
curl -X POST https://api.portfolio.dev.the-full-stack.com/contact \
  -H "Content-Type: application/json" \
  -H "X-Turnstile-Bypass: $(grep -m1 '^TURNSTILE_BYPASS_SECRET=' docker/env/server/.dev | cut -d= -f2-)" \
  -d '{
    "operation":"contact","action":"create",
    "name":"E2E Verify","email":"e2e@example.com","message":"verify"
  }'
# -> 200, fila en contacts, email enviado

# 6. Eliminar infra vieja en dev
aws lambda delete-function --function-name portfolio-stream-processor-dev --profile tfs-dev --region us-east-1
aws dynamodb delete-table --table-name portfolio-contacts-dev --profile tfs-dev --region us-east-1
aws dynamodb delete-table --table-name portfolio-tracking-dev --profile tfs-dev --region us-east-1
DLQ_URL=$(aws ssm get-parameter --name /portfolio/dev/sqs/stream-processor-dlq/url --profile tfs-dev --region us-east-1 --query Parameter.Value --output text)
aws sqs delete-queue --queue-url "$DLQ_URL" --profile tfs-dev --region us-east-1

# 7. Borrar SSM params huerfanos
for p in /portfolio/dev/dynamodb/contacts/name /portfolio/dev/dynamodb/contacts/arn \
         /portfolio/dev/dynamodb/contacts/stream-arn /portfolio/dev/dynamodb/tracking/name \
         /portfolio/dev/dynamodb/tracking/arn /portfolio/dev/dynamodb/tracking/stream-arn \
         /portfolio/dev/sqs/stream-processor-dlq/arn /portfolio/dev/sqs/stream-processor-dlq/url; do
  aws ssm delete-parameter --name "$p" --profile tfs-dev --region us-east-1 2>&1 | tail -1
done

# 8. Verificar AC-5 + AC-7 (resource-not-found)
aws dynamodb describe-table --table-name portfolio-contacts-dev --profile tfs-dev --region us-east-1 2>&1 | grep ResourceNotFoundException
aws lambda get-function --function-name portfolio-stream-processor-dev --profile tfs-dev --region us-east-1 2>&1 | grep ResourceNotFoundException
```

### B.3 stage (idem dev cambiando `--stage=dev` -> `--stage=stage`)

Mismos pasos B.2 con el perfil/stage correspondiente.

### B.4 prod (idem stage, pero EXTRA cuidado)

- Antes de los `delete-*`: snapshot manual de las tablas DDB con `aws dynamodb scan` + S3 backup (por si hay datos importantes)
- Confirmar que `contacts` en Neon prod tiene fila representativa antes de eliminar la tabla DDB

### Bucle de correccion

Si CUALQUIER paso falla:
1. Diagnosticar (logs CloudWatch, error de psycopg, error de AWS CLI)
2. Corregir (commit nuevo en feature branch, redeploy si es codigo)
3. Re-ejecutar la suite COMPLETA desde B.1 hacia adelante
4. No marcar Phase 5 completa con un comando fallando

## Regla de cierre

El PR `feature/direct-neon-writes -> dev` se mergea SOLO cuando:

- B.1, B.2 verdes (dev funciona)
- AC-1 a AC-7 verificables manualmente
- Los `delete-*` de B.2 pasos 6-7 ejecutados (infra vieja borrada en dev)
- El ultimo commit del PR incluye `git rm -r docs/specs/direct-neon-writes/`

Stage + prod (B.3 + B.4) se hacen DESPUES del merge a dev, en sus propios PRs de promocion (`dev -> stage` y `stage -> main`) per el flujo del proyecto.
