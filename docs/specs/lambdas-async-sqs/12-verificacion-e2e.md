# 12 — Verificacion E2E iterativa (seccion 11)

> Fase de cierre del plan. Es SIEMPRE la ultima fase y el ultimo commit
> (commit 15 de la seccion 10). NO se marca como completa hasta que la
> bateria completa pasa en verde. Push + PR ocurren UNICAMENTE despues.

[< 11](11-paralelizacion-worktrees.md) | [README >](README.md)

---

## Parte A — Refactor de tests

### Tests que se ELIMINAN

Ninguno. Los tests viejos del sync mode se mantienen detras del flag
ASYNC_MODE=false (preservan el rollback). Cuando el flag se elimine
post-merge, eliminar:

| Archivo | Cuando eliminar |
|---------|-----------------|
| `services/contact_form/tests/integration/test_email_failure_still_persists_e2e.py` | Tras eliminar el sync mode (PR aparte, post-deprecation) |
| `services/contact_form/tests/integration/test_valid_form_creates_contact_e2e.py` (rama sync) | Idem |
| `services/tracking_pixel/tests/integration/test_*_e2e.py` (rama sync) | Idem |

### Tests que se MODIFICAN

| Archivo | Cambio |
|---------|--------|
| `services/contact_form/tests/integration/test_valid_form_creates_contact_e2e.py` | Parametrizar con ASYNC_MODE=true/false |
| `services/contact_form/tests/integration/test_invalid_turnstile_returns_403_e2e.py` | Verificar que NO se encolo (mock SQS) |
| `services/contact_form/tests/integration/test_rate_limit_returns_429_e2e.py` | Idem |
| `services/contact_form/tests/integration/test_email_failure_still_persists_e2e.py` | RENOMBRAR a `..._sync_mode` (solo aplica a sync) |
| `services/tracking_pixel/tests/integration/test_user_agent_*_e2e.py` | MOVER al worker (ahora UA parsing es del worker) |
| `services/tracking_pixel/tests/integration/test_valid_event_persists_e2e.py` | RENOMBRAR a `..._sync_mode` |

### Tests que se CREAN

Documentados en cada fase (05-08). Total nuevos: ~30 tests (unit +
integration entre los 4 lambdas + shared/queue + shared/db).

### Barrido global

Verificar que ningun test viejo apunta a codigo removido:

```bash
# El sync path NO se removio (solo se gateo con flag) -> el barrido es
# para verificar que NO hay imports rotos accidentales.

rg -l "from services.contact_service import save_contact" serverless/lambda/ tests/
# Esperado: solo en services/contact_form/ y en services/contact_worker/
# (que copio el helper, NO desde shared) — y sus tests.

rg -l "from services.tracking_service import save_tracking_event" serverless/lambda/
# Esperado: solo en services/tracking_pixel/ y en services/tracking_worker/

rg -l "process_contact_form" serverless/lambda/
# Esperado: services/contact_form/ (sync mode) — NUNCA en contact_worker/.

rg -l "process_tracking_event" serverless/lambda/
# Esperado: services/tracking_pixel/ (sync mode) — NUNCA en tracking_worker/.
```

## Parte B — Bateria de comandos reales

### B.1 — Verificaciones que NO requieren AWS (obligatorias)

```bash
# Lint + format
pnpm exec biome check .

# Typecheck (no aplica al backend Python, pero verificar que las apps siguen OK)
pnpm exec tsc --noEmit
pnpm exec astro check

# Tests unit del backend Python (los 4 lambdas + shared/queue + shared/db)
python devtools/run.py serverless tests --type=unit --lambda=contact_form
python devtools/run.py serverless tests --type=unit --lambda=tracking_pixel
python devtools/run.py serverless tests --type=unit --lambda=contact_worker
python devtools/run.py serverless tests --type=unit --lambda=tracking_worker
python devtools/run.py serverless tests --type=unit --shared=queue
python devtools/run.py serverless tests --type=unit --shared=db

# Tests con cobertura
python devtools/run.py serverless tests --type=coverage --lambda=contact_worker
python devtools/run.py serverless tests --type=coverage --lambda=tracking_worker

# Devtools tests (cambios en provisioner.py + infra_provision.py)
cd devtools && python -m pytest tests/serverless/ -v

# Build estatico de las apps (no debe verse afectado)
pnpm run build
```

### B.2 — Verificaciones que requieren AWS dev (obligatorias antes de PR)

```bash
# Provisionamiento de infra (idempotente — segunda corrida es no-op)
python devtools/run.py serverless provision-infra --stage=dev --aws-profile=tfs-dev
# Esperado: cero errores; las 4 colas + 2 alarmas ya existen.

# Status de los 4 lambdas
python devtools/run.py serverless status --lambda=contact_form --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless status --lambda=tracking_pixel --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless status --lambda=contact_worker --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless status --lambda=tracking_worker --stage=dev --aws-profile=tfs-dev

# Tests de integration contra dev (Neon dev + moto SES + SQS dev real)
python devtools/run.py serverless tests --type=integration --lambda=contact_worker
python devtools/run.py serverless tests --type=integration --lambda=tracking_worker

# Verificar Event Source Mappings
aws lambda list-event-source-mappings --function-name portfolio-contact-worker-dev \
  --profile tfs-dev | jq '.EventSourceMappings[] | {UUID, State, BatchSize}'
# Esperado: 1 mapping con State=Enabled, BatchSize=1.

aws lambda list-event-source-mappings --function-name portfolio-tracking-worker-dev \
  --profile tfs-dev | jq '.EventSourceMappings[] | {UUID, State, BatchSize, FunctionResponseTypes}'
# Esperado: 1 mapping con State=Enabled, BatchSize=10, FunctionResponseTypes=[ReportBatchItemFailures].

# Verificar alarmas
aws cloudwatch describe-alarms \
  --alarm-names portfolio-contact-form-dlq-not-empty-dev \
                portfolio-tracking-events-dlq-not-empty-dev \
  --profile tfs-dev | jq '.MetricAlarms[] | {AlarmName, StateValue}'
# Esperado: ambas en OK (DLQs vacias).
```

### B.3 — Smoke E2E contra API publica dev

```bash
# 1. POST /track con evento valido (deberia responder 202 en <500ms)
curl -X POST 'https://api.portfolio.dev.the-full-stack.com/track' \
  -H 'Content-Type: application/json' \
  -H 'Origin: https://portfolio.dev.the-full-stack.com' \
  -d '{
    "operation": "tracking",
    "action": "track",
    "session_id": "smoke-001",
    "event_id": "01900000-0000-7000-0000-000000000001",
    "event_type_id": "...",
    "page_path": "/smoke",
    "viewport_width": 1920,
    "viewport_height": 1080
  }' \
  -w '\nstatus=%{http_code} time=%{time_total}s\n'
# Esperado: status=202, time<0.5s, body con {page_id, session_id, created_at, accepted: true}.

# 2. Verificar que el evento llego a Neon dev (en <30s)
PGPASSWORD=... psql -h ep-... -U ... -d neondb -c \
  "SELECT page_id, session_id, page_path FROM vis_tracking_events WHERE session_id='smoke-001';"
# Esperado: 1 fila con el evento.

# 3. POST /contact con form valido (necesita Turnstile token real o bypass dev)
curl -X POST 'https://api.portfolio.dev.the-full-stack.com/contact' \
  -H 'Content-Type: application/json' \
  -H 'Origin: https://portfolio.dev.the-full-stack.com' \
  -H 'X-Turnstile-Bypass: <bypass-secret-dev>' \
  -d '{
    "operation": "contact",
    "action": "create",
    "name": "Smoke Test",
    "email": "smoke@example.com",
    "message": "E2E test del plan lambdas-async-sqs",
    "cf_token": "bypass"
  }' \
  -w '\nstatus=%{http_code} time=%{time_total}s\n'
# Esperado: status=202, time<0.8s, body con {contact_id, created_at, accepted: true}.

# 4. Verificar el contact en Neon dev
psql ... -c "SELECT id, email FROM contacts WHERE email='smoke@example.com';"
# Esperado: 1 fila.

# 5. Verificar el email recibido (CloudWatch del worker)
aws logs tail /aws/lambda/portfolio-contact-worker-dev --since 5m --profile tfs-dev | \
  grep 'owner email sent'
# Esperado: log "owner email sent" con el contact_id matching.

# 6. Cleanup: borrar las filas de prueba
psql ... -c "DELETE FROM vis_tracking_events WHERE session_id='smoke-001';"
psql ... -c "DELETE FROM contacts WHERE email='smoke@example.com';"
```

### B.4 — Smoke de idempotencia (re-encolar mismo mensaje)

```bash
# 1. Encolar manualmente un mensaje al contact-form queue con un contact_id fijo
TEST_ID='01900000-0000-7000-0000-aaaaaaaaaa01'
aws sqs send-message --profile tfs-dev \
  --queue-url $(aws ssm get-parameter --name /portfolio/dev/sqs/contact-form/url \
                  --query 'Parameter.Value' --output text --profile tfs-dev) \
  --message-body "$(cat <<EOF
{
  "schema_version": 1,
  "contact_id": "$TEST_ID",
  "created_at": "2026-06-01T00:00:00+00:00",
  "session_id": "idempotency-test",
  "name": "Idempotency",
  "email": "idem@example.com",
  "message": "Test idempotencia E2E",
  "ip": "127.0.0.1"
}
EOF
)"

# 2. Esperar 10s y verificar que se procesa
sleep 10
psql ... -c "SELECT COUNT(*) FROM contacts WHERE id='$TEST_ID';"
# Esperado: 1.

# 3. Encolar el MISMO mensaje de nuevo
aws sqs send-message ... # mismo body

# 4. Esperar 10s y verificar que NO duplica
sleep 10
psql ... -c "SELECT COUNT(*) FROM contacts WHERE id='$TEST_ID';"
# Esperado: 1 (no 2). Y CloudWatch del worker debe mostrar
# 'contact already persisted, skipping email' en el 2do procesamiento.
```

### B.5 — Smoke del rollback (ASYNC_MODE=false)

```bash
# 1. Cambiar el flag en el manifest del contact_form dev
# (editar services/contact_form/manifest.yaml: ASYNC_MODE: 'false' en env.dev)
python devtools/run.py serverless deploy --lambda=contact_form --stage=dev --aws-profile=tfs-dev

# 2. POST /contact con form valido
curl -X POST .../contact ...
# Esperado: status=201 (no 202), body con shape sync (contact_id + email enviado).

# 3. Verificar que el contact se persiste (en el path sync, no via SQS)
psql ... -c "SELECT ... FROM contacts WHERE email='rollback-test@example.com';"

# 4. Restaurar ASYNC_MODE=true y redeploy
# (revertir manifest.yaml)
python devtools/run.py serverless deploy --lambda=contact_form --stage=dev --aws-profile=tfs-dev
```

## Parte C — Bucle de correccion ("no parar hasta que funcione")

```text
ejecutar comando (B.1 -> B.2 -> B.3 -> B.4 -> B.5)
   |
   v
{paso?}-- si --> siguiente comando
   |
   no
   v
diagnosticar:
   - leer stderr completo
   - aws logs tail /aws/lambda/<lambda>-dev --since 5m
   - aws sqs get-queue-attributes para ver mensajes inflight / visibles
   - psql para inspeccionar el estado de la DB
   |
   v
corregir codigo o test
   |
   v
re-ejecutar la suite afectada + el comando que fallo
   |
   +--> volver a "ejecutar comando"
```

### Casos comunes de fallo + diagnostico

| Sintoma | Causa probable | Comando de diagnostico |
|---------|----------------|------------------------|
| HTTP 502 en /contact async | `send_to_queue` falla (SSM path mal, IAM mal) | `aws logs tail .../contact-form-dev --since 5m` |
| 202 pero el contact NO llega a Neon | Event Source Mapping no creado o disabled | `aws lambda list-event-source-mappings ...` |
| Workers fallan con `RuntimeError: SSM_NEON_URL_PATH no seteada` | El manifest del worker no declara `secrets: [neon-url]` o devtools no inyecto la env var | `aws lambda get-function-configuration ...` |
| Mensaje queda inflight 5+ min | Worker timeout > visibility_timeout | Verificar `visibility_timeout_seconds` >= 6x timeout en YAML |
| DLQ recibe mensajes | El worker crashea repetidamente | `aws logs tail` del worker; `aws sqs receive-message` de la DLQ para ver el body |
| Email duplicado en idempotencia smoke | `save_contact_idempotent` no retorna False en duplicado | Verificar `rowcount` en el helper |
| `InFailedTransactionError` en tracking_worker | Falta `session.begin_nested()` por mensaje | Ver fase 06 |

## Regla de cierre

Esta fase NO se marca completa mientras quede UN comando fallando, UN
test rojo, o coverage <80%. Iterar — corregir, re-ejecutar, repetir —
hasta que toda la bateria pase. Solo entonces el PR esta listo.

## Gate de cierre: push + PR

```text
bateria Parte B (B.1 + B.2 + B.3 + B.4 + B.5) en VERDE
                       |
                       v
git rm -r docs/specs/lambdas-async-sqs/
git add -A
git commit -m "test(specs): verificacion E2E + cleanup spec lambdas-async-sqs"
                       |
                       v
git push origin feature/lambdas-async-sqs
gh pr create --base dev --title "feat: lambdas async via SQS + DLQ + CloudWatch" \
             --body "<segun git-workflow.md: Problema / Solucion / Como probar / TODO>"
```

NUNCA hacer `push` ni abrir el PR con la bateria fallando.

### Body del PR

```markdown
## Problema

1. `/track` y `/contact` tardan 8-12s en responder por el cold-start de
   Neon. Mala UX y stress en API Gateway (timeout 30s).
2. El frontend espera respuesta sincronica pero no usa el `contact_id` —
   nada justifica el bloqueo.
3. Sin DLQ ni alarmas si los writes a Neon fallan -> leads perdidos.

## Solucion

1. Introduje 2 colas SQS + 2 workers Lambda (`contact_worker`,
   `tracking_worker`). Las Lambdas HTTP existentes pasan a ser **encoders**
   ligeros: validan, rate-limit, Turnstile (en /contact), encolan a SQS y
   responden 202 inmediato (<800ms p95).
2. Pre-genere `contact_id` UUIDv7 en el encoder, lo devuelvo en el body
   del 202 y el worker lo usa con `ON CONFLICT (id) DO NOTHING` para
   idempotencia.
3. DLQ + retry x3 + CloudWatch alarm por DLQ no-vacia. Feature flag
   `ASYNC_MODE` para rollback rapido sin redeploy.

## Como probar

Copiar la bateria de comandos de la seccion 11 del plan (Parte B.1
hasta B.5). Resumen rapido:

​```bash
# Unit
python devtools/run.py serverless tests --type=unit --lambda=<X>  # x4

# Smoke contra dev (requiere AWS profile tfs-dev)
curl -X POST https://api.portfolio.dev.the-full-stack.com/track -d '...'
# Esperado: 202 en <500ms, evento en Neon en <30s.

curl -X POST https://api.portfolio.dev.the-full-stack.com/contact -d '...'
# Esperado: 202 en <800ms con contact_id, contact en Neon + email en <30s.
​```

## TODO

- [ ] Post-deploy en prod (1-2 semanas estable): eliminar el feature flag
  `ASYNC_MODE` y la rama sync legacy del codigo (PR aparte).
- [ ] Promover el patron "encoder + worker SQS" a una rule
  `.claude/rules/sqs-worker-pattern.md` si lo aplicamos a futuros
  endpoints.
- [ ] Considerar `SnapStart` para los workers cuando el cold-start sea
  visible (ya no impacta al cliente, pero acelera retries de DLQ).
```

## AC cubiertos por la bateria

Toda la fase 11 cubre los 19 AC:

- B.1 cubre AC-1..AC-14 (unit + integration)
- B.2 cubre AC-15, AC-16, AC-17 (provisioning real verificado)
- B.3 cubre AC-18, AC-19 (smoke E2E)
- B.4 cubre AC-10, AC-14 (idempotencia en vivo)
- B.5 cubre AC-5, AC-18 (rollback funcional)

## Anti-patrones de la verificacion final

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Declarar listo con B.3 fallando "lo veo en logs" | Logs != verificacion automatizada | Bloquea hasta que el comando retorne OK |
| Smoke contra `localhost` (modo direct) | NO valida el ESM ni la integracion AWS | Smoke contra `api.portfolio.dev` |
| Saltar B.5 (rollback) | Si falla el rollback en prod, no hay backup | Verificar SIEMPRE el rollback antes del merge |
| `git push --no-verify` | Bypassea pre-push hooks | Fix el hook o el codigo |
| PR mergeado sin que el smoke pase | El plan no esta listo | El smoke es el GATE |
| Olvidar `git rm -r docs/specs/lambdas-async-sqs/` | La spec es efimera | Ultimo commit la elimina |

---

[< 11](11-paralelizacion-worktrees.md) | [README >](README.md)
