# 02 — Flujos de los Lambdas

> [<- 01-arquitectura](01-arquitectura-5-stacks.md) | [Siguiente: 03-datos ->](03-datos.md)

Diagramas de flujo de cada uno de los 4 Lambdas. Cada Lambda sigue el
formato `lambda-controller`: el `handler.py` (dentro de `core/`) es un
router delgado que sintetiza un evento `{operation, action, data}` y
delega en un controller; el controller orquesta llamando a un service.

## 1. `contact_form` — POST /contact

Atiende el form de contacto: valida, rate-limit, Turnstile, persiste y
notifica por email. Stack `portfolio-contact-form-<stage>`.

```text
Browser (ContactForm.astro en *.the-full-stack.com)
   | POST /contact  body: {name, email, message, service_type,
   |                       company, role, budget, timeline, cf_token}
   v
Cloudflare upstream         Capa 0: DDoS L3/L4/L7 + Bot Fight (free)
   |                        inyecta CF-Connecting-IP, CF-IPCountry
   v
API Gateway REST            Capa 2: throttling global (burst 5, 1/s)
  POST /contact             (metodo agregado por este stack sobre la
   |                         API del stack de infra)
   v
Request Validator           Capa 3: JSON Schema — body shape, required,
   |                         lengths, cf_token presente
   |  schema OK?  --NO--> 400 (sin invocar el Lambda — ahorra costo)
   v  YES
==================================================================
 Lambda contact_form  (core/handler.lambda_handler)
   |
   |  handler arma  {operation:'contact', action:'create', data:{...}}
   |  -> controllers/contact/create.Create.run()
   v
 preload   resuelve config (SSM paths) desde AppConfig
   |
 validate  models/contact.py (Pydantic) valida 'data'
   |
 execute   -> services/contact_service.py:
   |
   +--(a) extract_ip(event)   CF-Connecting-IP > X-Forwarded-For
   |
   +--(b) rate-limit per-IP   shared/rate_limit/ — 3 req/5min/IP
   |        deny? --> 429 Retry-After
   |
   +--(c) Turnstile siteverify (httpx -> challenges.cloudflare.com)
   |        verifica success + hostname en whitelist + ts < 5min
   |        invalido? --> 403 + metric BotBlocked
   |        secret leido de SSM, cacheado con shared/cache (TTL 300s)
   |
   +--(d) persistence -> DynamoDB PUT contacts (id=UUIDv7)
   |        ConditionExpression attribute_not_exists(id)   <10ms p99
   |
   +--(e) notification -> SES SendEmail al owner (HTML + texto)
   |
   v
 {is_valid, code:0, data:{contact_id}}
   |
   v
 200 OK { ok:true, contact_id, message:"Gracias" }
   |
   |  === ASINC: el INSERT en contacts emite un DynamoDB Stream record ===
   v  (lo consume stream_processor — ver seccion 3)

Observabilidad transversal: CloudWatch Logs JSON (Powertools, retention
7d) + X-Ray. Sin alarmas operacionales.
```

## 2. `tracking_pixel` — POST /track

Registra eventos de tracking (page views, clicks). Stack
`portfolio-tracking-pixel-<stage>`.

```text
Browser (TrackingPixel.astro, client:idle)
   |  lee consent cookie (GDPR opt-in)  --NO--> SKIP, no track
   |  YES: recolecta signals (UA, viewport, UTMs, referrer,
   |       lang, timezone, session_id) + token Turnstile invisible
   v
   | POST /track  body: {...signals, cf_token}
   v
Cloudflare upstream         Capa 0 (free)
   v
API Gateway REST            Capa 2: throttling global (burst 60)
  POST /track
   v
Request Validator           Capa 3: JSON Schema del payload
   |  schema OK?  --NO--> 400
   v  YES
==================================================================
 Lambda tracking_pixel  (core/handler.lambda_handler)
   |
   |  handler arma  {operation:'track', action:'create', data:{...}}
   |  -> controllers/track/create.Create.run()
   v
 preload / validate (Pydantic)
   |
 execute  -> services/track_service.py:
   |
   +--(a) rate-limit per-IP   shared/rate_limit/ — 30 req/5min/IP
   |
   +--(b) enrichment   CF-Connecting-IP, CF-IPCountry, parse User-Agent
   |        (device, browser, os) — parsing cacheado con shared/cache
   |
   +--(c) calcula TTL  expires_at = now + 60 dias
   |
   +--(d) persistence -> DynamoDB PUT tracking
   |        (PK session_id, SK page_id=UUIDv7, expires_at)
   v
 204 No Content + CORS headers   (sin payload, no UX impact)
   |
   |  === ASINC: el INSERT en tracking emite un Stream record ===
   v  (lo consume stream_processor)
```

## 3. `stream_processor` — DynamoDB Streams -> Neon

Replica los cambios de las tablas `contacts` y `tracking` a Neon
PostgreSQL. Stack `portfolio-stream-processor-<stage>`. Trigger
`on-table-changes`: devtools conecta los Event Source Mappings de ambos
Streams + la DLQ.

```text
DynamoDB tabla contacts  o  tracking
   |  INSERT / MODIFY / REMOVE
   v
DynamoDB Streams (NEW_AND_OLD_IMAGES, retencion 24h)
   |  batch (batchSize=100, maxBatchingWindow=10s)
   v
==================================================================
 Lambda stream_processor  (core/handler.lambda_handler)
   |  Reserved concurrency baja: protege el connection pool de Neon
   |
   |  handler recibe event['Records'][] del Stream
   |  -> controllers/.../create (uno por record)
   v
 execute -> services/stream_service.py, por cada record:
   |
   +--(a) idempotency check
   |        SELECT 1 FROM processed_stream_events WHERE event_id=?
   |        ya procesado? -> skip
   |
   +--(b) transforma  DynamoDB Item {"id":{"S":...}} -> dict plano
   |
   +--(c) Neon connection (psycopg3 v3, endpoint pooled, SSL)
   |        connection cacheada en module scope (cold start);
   |        connection string leida de SSM (neon-url), cacheada
   |
   +--(d) UPSERT  INSERT ... ON CONFLICT (stream_event_id) DO NOTHING
   |
   +--(e) INSERT processed_stream_events (event_id, ...)
   v
 batch OK?  --NO (excepcion)--> el Lambda reintenta (x3, backoff)
   |                            tras 3 fallos -> DLQ SQS
   v
 Neon actualizado (lag tipico 5-30s desde el write a DynamoDB)
```

> El schema de Neon lo gestionan los modelos SQLAlchemy de
> `serverless/src/_shared/db/` + Alembic. El `stream_processor` usa ese
> ORM para escribir. Ver [03-datos.md](03-datos.md).

## 4. `db` — gestion del schema (invoke directo)

Corre las migraciones Alembic del schema PostgreSQL dentro de AWS. Stack
`portfolio-db-<stage>`. Trigger `direct`: no tiene ruta HTTP, se invoca
con `aws lambda invoke` (o via devtools).

```text
Operador / devtools / deploy hook
   |  aws lambda invoke  payload: {"command": <cmd>, "args": {...}}
   v
==================================================================
 Lambda db  (core/handler.lambda_handler)
   |
   |  handler arma  {operation:'db', action:<command>, data:<args>}
   |  -> controllers/db/<command>
   v
 execute -> services/db_service.py:
   |
   +-- resuelve la connection string de Neon desde SSM (neon-url)
   |
   +-- corre Alembic contra Neon segun el command:
   |
   |   command: migrate          -> alembic upgrade head
   |   command: migrate +target  -> alembic upgrade <rev>
   |   command: current          -> revision aplicada
   |   command: show-migrations  -> historial
   |   command: downgrade        -> alembic downgrade (requiere confirm)
   |   command: stamp            -> adopta una rev sin recrear tablas
   v
 {is_valid, code, data:{...}}
```

Comandos via devtools (`db-migrate`, `db-rollback`, `db-current`, ...) —
ver [04-deploy-operacion.md](04-deploy-operacion.md). Operacion de Neon:
[.claude/rules/neon-management.md](../../rules/neon-management.md).

## 5. Defense in depth (capas)

El backend no usa AWS WAF. La defensa per-IP la da un middleware
self-managed con DynamoDB. Capas de afuera hacia adentro:

| Capa | Mecanismo | Costo |
|------|-----------|-------|
| 0 | Cloudflare upstream — DDoS L3/L4/L7 + Bot Fight; inyecta `CF-Connecting-IP` / `CF-IPCountry` | $0 |
| 1 | Middleware rate-limit per-IP (`shared/rate_limit/`, DynamoDB sliding window): `/contact` 3 req/5min, `/track` 30 req/5min; white/blacklist; auto-blacklist si 3+ tokens Turnstile validos en 60s | $0 |
| 1.5 | Reserved concurrency del Lambda (defensa pasiva: AWS retorna 429 sin invocar si se excede) | $0 |
| 2 | API Gateway throttling — GLOBAL, no per-IP (burst + steady rate) | $0 |
| 3 | Request Validator — JSON Schema rechaza con 400 antes de invocar el Lambda | $0 |
| 4 | Business logic del Lambda — Turnstile siteverify, validacion Pydantic | $0 |
| 5 | Observabilidad — CloudWatch Logs 7d + X-Ray; sin alarmas operacionales | $0 |

Detalle del rate-limit: skill `serverless-rate-limit`. Detalle de
Turnstile: skill `cloudflare-turnstile`.

---

[<- 01-arquitectura](01-arquitectura-5-stacks.md) | [Siguiente: 03-datos ->](03-datos.md)
