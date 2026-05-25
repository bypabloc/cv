# 01 — Contexto, Solucion y Criterios de Aceptacion

> Secciones 1, 2 y 3 del plan-format. Define el problema, la solucion
> convergente y los AC numerados que tests y tareas referencian.

[< README](README.md) | [Siguiente: 02 — Recursos SQS + CloudWatch >](02-resources-sqs-cloudwatch.md)

---

## 1. Contexto / Problema

### Sintoma observado

Cuando el usuario invoca `POST /track` o `POST /contact` desde el portfolio en
prod o dev, la respuesta HTTP tarda **8-12 segundos**. La causa principal es
el cold-start de Neon PostgreSQL: el compute auto-suspende tras 5 min de
inactividad y necesita ~3-8s para reanudarse en la primera conexion (esperable
en el plan free de Neon).

El flujo actual es completamente sincronico end-to-end:

```text
Cliente -> API Gateway -> Lambda HTTP -> rate-limit (DDB ~50ms)
        -> [Turnstile siteverify (~200-400ms)]   (solo /contact)
        -> Neon connect + UPSERT session + INSERT data  (~8-12s en cold-start)
        -> [SES SendEmail (~500ms)]               (solo /contact)
        -> respuesta HTTP al cliente
```

Implicancias:
- El cliente espera hasta 12s viendo un spinner. Mala UX.
- API Gateway tiene timeout 30s; estamos cerca del limite.
- `/track` envia con `navigator.sendBeacon` desde el browser pero el usuario
  igual percibe lentitud si abre la consola o si el evento bloquea la
  navegacion subsiguiente.
- `/contact`: el cliente solo necesita confirmacion de "lo recibimos"; el
  `contact_id` se retorna pero el front no lo usa.
- El email del owner (SES) tampoco es critico en tiempo: 5-15s post-submit es
  aceptable para una notificacion de form de contacto.

### Hallazgos de exploracion

Codigo revisado:
- [tracking_pixel/core/handler.py](../../serverless/lambda/services/tracking_pixel/core/handler.py) +
  [controllers/tracking/track.py](../../serverless/lambda/services/tracking_pixel/core/controllers/tracking/track.py) +
  [services/tracking_service.py](../../serverless/lambda/services/tracking_pixel/core/services/tracking_service.py)
- [contact_form/core/handler.py](../../serverless/lambda/services/contact_form/core/handler.py) +
  [controllers/contact/create.py](../../serverless/lambda/services/contact_form/core/controllers/contact/create.py) +
  [services/contact_service.py](../../serverless/lambda/services/contact_form/core/services/contact_service.py)
- [shared/db/session.py](../../serverless/lambda/shared/db/session.py),
  [shared/db/repository.py](../../serverless/lambda/shared/db/repository.py)
- [devtools/serverless/infra_provision.py](../../devtools/serverless/infra_provision.py)
  (ya soporta `kind: sqs-queue` basico; falta `redrive_policy` +
  `visibility_timeout_seconds` + Event Source Mapping para `trigger.type: sqs`)
- [devtools/serverless/provisioner.py](../../devtools/serverless/provisioner.py)
  (define `_VALID_TRIGGERS = ('direct', 'http')` — hay que agregar `sqs`)

Conclusiones:
- El ORM es sync (SQLAlchemy 2.x + psycopg v3 + NullPool). Cambiar a async
  (asyncio) NO arregla el cold-start: solo cambia el modelo de concurrencia.
  Lo que hay que cambiar es la TOPOLOGIA: desacoplar la respuesta del trabajo.
- `Contact.id` ya es PK UUID -> `ON CONFLICT (id) DO NOTHING` es trivial.
- `TrackingEvent` tiene PK compuesta `(created_at, visit_id, page_id)`.
  Como `visit_id` lo resuelve `ensure_session_and_visit` en el worker
  (depende del UPSERT de session), la idempotencia se monta sobre la PK
  completa: pre-generamos `created_at` y `page_id` en la HTTP; `visit_id`
  lo resuelve el worker; el INSERT con `ON CONFLICT` no-opera si SQS
  re-entrega el mismo mensaje (el visit ya existe gracias al UPSERT).
- `shared/lambda_kit/http_handler` ya soporta inyectar `_meta` desde el
  evento HTTP. Podemos reutilizarlo en los encoders sin tocarlo.
- `devtools/serverless/provisioner.py` traduce `manifest.yaml` a llamadas AWS
  CLI; hay que extender el conjunto de triggers con `sqs` y wirear el
  Event Source Mapping (`aws lambda create-event-source-mapping`).

---

## 2. Solucion Propuesta

### Approach

Introducir 2 colas SQS standard (no FIFO — el orden no importa, el throughput
y el coste son criticos) y 2 Lambdas workers nuevos:

```text
ANTES:
  Cliente -> Lambda HTTP (rate-limit + Turnstile + Neon + SES) -> 201/204 (8-12s)

DESPUES:
  Cliente -> Lambda HTTP "encoder" (rate-limit + Turnstile + encolar) -> 202 (200-600ms)
                                |
                                v
                        SQS portfolio-{contact-form,tracking-events}-${stage}
                                |
                                v
                        Lambda worker (Neon + SES)
                                |
                                v
                       OK -> ack SQS  |  Fail -> retry x3 -> DLQ -> CloudWatch alarm
```

Las Lambdas HTTP existentes pasan a ser **encoders ligeros**:
- Validan input (Pydantic) y rechazan 400.
- Aplican rate-limit (sliding window DynamoDB).
- `/contact`: verifican Turnstile (HTTP a Cloudflare) y cuentan auto-blacklist.
- Generan los UUIDv7 (`contact_id`, `page_id`) y los meten en el mensaje SQS
  junto con `created_at`.
- Publican a SQS via `boto3.client('sqs').send_message()`.
- Responden `202 Accepted` (con `contact_id` en el caso de `/contact`).

Los workers nuevos:
- `contact_worker`: trigger SQS batch=1, escribe a Neon (UPSERT session +
  INSERT contact con `ON CONFLICT id DO NOTHING`) y envia email SES.
- `tracking_worker`: trigger SQS batch=10 con `ReportBatchItemFailures`,
  escribe events a Neon en una sola conexion compartida.

Feature flag `ASYNC_MODE` (env var del encoder):
- `ASYNC_MODE=true` -> encolar y responder 202 (modo nuevo).
- `ASYNC_MODE=false` -> ejecutar el flujo sync actual (rollback).

### Decisiones clave

- **Decision 1**: SQS standard, NO FIFO. Razon: orden no importa, throughput
  free tier 1M req/mes basta para 50k tracking events + 200 contacts/mes; FIFO
  costaria 5x mas y agregaria latencia.
- **Decision 2**: 2 colas + 2 workers (no 1 cola con discriminator). Razon:
  aislamiento de fallos (tracking puede caer sin afectar emails) + permite
  batch_size diferente.
- **Decision 3**: Idempotencia via UUIDv7 + `ON CONFLICT DO NOTHING` (no
  Powertools `@idempotent`). Razon: el costo DynamoDB de Powertools idempotency
  es innecesario cuando ya tenemos PK natural; UUIDv7 es time-ordered y
  determiniza el destino.
- **Decision 4**: Turnstile + rate-limit + auto-blacklist quedan en la
  Lambda HTTP, NO se mueven al worker. Razon: la deteccion de bots ("3+ tokens
  validos en 60s") debe correr ANTES de encolar para no inflar SQS con basura;
  el rechazo 429/403 debe llegar al cliente sincronicamente.
- **Decision 5**: Workers reciben `ip`/`country`/`user_agent`/`origin` como
  parte del mensaje SQS (la HTTP los extrae del request y los serializa).
  Razon: los workers no tienen request HTTP; los datos viajan con el mensaje.
- **Decision 6**: Feature flag de env var (no DynamoDB ni Parameter Store).
  Razon: el flag se setea en el `manifest.yaml` del encoder; cambiar requiere
  redeploy pero el redeploy es <30s; mas simple y auditable.
- **Decision 7**: La spec sigue el patron lambda-controller para los workers
  (mismo `operation + action`, `controller`, `service`, `model`). El trigger
  SQS se mapea a `operation=worker, action=process` por convencion (el worker
  no recibe operation/action del payload — los hardcodea).

---

## 3. Criterios de Aceptacion (BDD)

Numerados estables, referenciados por tests y tareas. Cubren happy path,
edge cases y errores.

### Encoder /contact

- **AC-1**: Given un cliente envia `POST /contact` con form valido + Turnstile
  token valido, When la Lambda `contact_form` procesa la request con
  `ASYNC_MODE=true`, Then responde `HTTP 202` con body
  `{contact_id: <uuidv7>, accepted: true}` en <800ms p95.

- **AC-2**: Given un cliente envia `POST /contact` con Turnstile invalido,
  When la Lambda `contact_form` procesa la request con `ASYNC_MODE=true`,
  Then responde `HTTP 403` SIN encolar nada en SQS.

- **AC-3**: Given un cliente envia `POST /contact` desde una IP rate-limited,
  When la Lambda `contact_form` procesa la request con `ASYNC_MODE=true`,
  Then responde `HTTP 429` SIN encolar nada en SQS.

- **AC-4**: Given un cliente envia `POST /contact` con form invalido (email
  malformado, message <10 chars, etc), When la Lambda procesa, Then responde
  `HTTP 400` con detalle del error SIN encolar.

- **AC-5**: Given la Lambda `contact_form` corre con `ASYNC_MODE=false`,
  When un cliente envia `POST /contact` valido, Then la Lambda ejecuta el
  flujo sync actual (UPSERT + SES + 201) sin tocar SQS.

### Encoder /track

- **AC-6**: Given un cliente envia `POST /track` con evento valido, When la
  Lambda `tracking_pixel` procesa con `ASYNC_MODE=true`, Then responde
  `HTTP 202` en <500ms p95.

- **AC-7**: Given un cliente envia `POST /track` desde IP rate-limited,
  When la Lambda procesa con `ASYNC_MODE=true`, Then responde `HTTP 429`
  SIN encolar.

- **AC-8**: Given un cliente envia `POST /track` con body invalido (sin
  `session_id`, viewport faltante, etc), When la Lambda procesa, Then
  responde `HTTP 400` SIN encolar.

### Worker `contact_worker`

- **AC-9**: Given un mensaje SQS valido con `contact_id` UUIDv7, When
  `contact_worker` procesa, Then UPSERTea `sessions` + `session_visits` +
  INSERTea en `contacts` y manda email via SES.

- **AC-10**: Given SQS re-entrega el mismo mensaje (mismo `contact_id`),
  When `contact_worker` procesa la 2da vez, Then el INSERT es no-op
  (`ON CONFLICT (id) DO NOTHING`) y NO manda email duplicado.

- **AC-11**: Given el envio de email SES falla (transient), When
  `contact_worker` procesa, Then el contact ya persistido NO se reinserta y
  el error de SES marca el item como `batchItemFailure` para retry.

### Worker `tracking_worker`

- **AC-12**: Given un batch SQS con 10 eventos validos, When
  `tracking_worker` procesa, Then UPSERTea sessions/visits y INSERTea los 10
  events compartiendo la misma conexion Neon.

- **AC-13**: Given un batch SQS con 10 eventos donde 2 fallan, When
  `tracking_worker` procesa, Then los 8 exitosos commitean y devuelve
  `batchItemFailures` con los 2 fallidos para retry.

- **AC-14**: Given SQS re-entrega un evento tracking ya procesado, When
  `tracking_worker` lo procesa de nuevo, Then el INSERT es no-op
  (`ON CONFLICT (created_at, visit_id, page_id) DO NOTHING`).

### Infraestructura

- **AC-15**: Given el manifest declara `trigger.type: sqs`, When devtools
  hace `serverless deploy`, Then crea el Event Source Mapping con
  `batch_size` y `function_response_types=[ReportBatchItemFailures]`.

- **AC-16**: Given el YAML `sqs/contact-form-queue.yaml` declara
  `redrive_policy: {target: portfolio-contact-form-dlq-${stage}, max_receive_count: 3}`,
  When devtools hace `serverless provision-infra`, Then la cola principal
  queda atada a la DLQ con `maxReceiveCount=3`.

- **AC-17**: Given un mensaje en la DLQ, When la metrica
  `ApproximateNumberOfMessagesVisible` >0 por >5 min, Then la alarma
  CloudWatch `portfolio-contact-form-dlq-not-empty-${stage}` entra en
  estado ALARM.

### Operacion

- **AC-18**: Given el feature flag `ASYNC_MODE` se cambia en el
  `manifest.yaml` y se hace `serverless deploy --lambda=contact_form
  --stage=dev`, When el cliente envia `/contact`, Then el comportamiento
  refleja el flag desde el cold-start siguiente sin redeploy de los
  workers ni del worker.

- **AC-19**: Given el deploy completo en `dev`, When se ejecuta un smoke
  test contra `https://api.portfolio.dev.the-full-stack.com/track` con
  un evento valido, Then se recibe HTTP 202 en <500ms y el evento queda
  persistido en Neon dentro de 30s.

### Total de AC: 19

Cada AC tiene al menos un test (unit o integration) que lo cubre. Ver la
matriz en cada `.md` de fase.

---

[< README](README.md) | [Siguiente: 02 — Recursos SQS + CloudWatch >](02-resources-sqs-cloudwatch.md)
