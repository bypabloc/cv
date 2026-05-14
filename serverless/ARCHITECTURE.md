# Arquitectura del backend serverless del portfolio

> Estructura completa de archivos y carpetas + diagrama de flujo del
> backend del form de contacto y tracking pixel del portfolio. Basado en
> la investigacion consolidada en `.claude/docs/{aws-lambda,aws-api-gateway,aws-dynamodb,aws-ses,cloudflare-turnstile,postgresql-18-analytics,neon}/`.
>
> **Region**: us-west-2 (Oregon)
> **Runtime**: Python 3.13 (managed runtime, arm64 Graviton2)
> **IaC**: AWS SAM
> **Storage hibrido**: DynamoDB (hot path, writes) + Neon PostgreSQL 18 (analytics, queries)
> **CLI**: `python devtools/run.py serverless <command>` (ver devtools/serverless/README.md)
> **Costo estimado**: ~$0.81/mes (sin WAF; rate-limit self-managed con DynamoDB; Neon free tier perpetuo)

---

## 1. Estructura completa de carpetas

```text
serverless/
│
├── README.md                            # Indice navegable de la carpeta
├── ARCHITECTURE.md                      # Este archivo (estructura + diagramas)
├── DEPLOYMENT.md                        # Pasos exactos para deploy primera vez
├── RUNBOOK.md                           # Operaciones (rotar secrets, ver logs, alarms)
│
├── template.yaml                        # SAM template: 5 Lambdas + API GW + DynamoDB tables + SES + IAM (sin WAF)
├── samconfig.toml                       # Config SAM por ambiente (dev, prod)
├── pyproject.toml                       # Dependencias compartidas (uv-managed)
├── uv.lock                              # Lockfile reproducible
├── .gitignore                           # .aws-sam/, .venv/, *.zip, samconfig.toml.local
├── Makefile                             # Atajos: make build / deploy / logs / clean
│
├── src/                                 # Codigo de los handlers Python
│   │
│   ├── common/                          # Modulo compartido entre Lambdas (layer opcional)
│   │   ├── __init__.py
│   │   ├── config.py                    # Settings desde env vars + SSM (Pydantic)
│   │   ├── logger.py                    # Powertools Logger configurado
│   │   ├── tracer.py                    # Powertools Tracer (X-Ray)
│   │   ├── metrics.py                   # Powertools Metrics (CloudWatch EMF)
│   │   ├── responses.py                 # JSON response helpers (200/400/429/500 + CORS)
│   │   ├── cors.py                      # Whitelist 6 subdominios + Gateway Response helper
│   │   ├── exceptions.py                # ApplicationError + ValidationError + TurnstileError
│   │   ├── dynamodb_client.py           # boto3.resource('dynamodb') en module scope
│   │   ├── ses_client.py                # boto3.client('sesv2') en module scope
│   │   ├── ssm_client.py                # SSM Parameter Store + KMS decrypt (Powertools parameters)
│   │   ├── ip_extractor.py              # Lee CF-Connecting-IP (priority) o X-Forwarded-For
│   │   ├── ulid.py                      # UUIDv7 generator (sorted by time)
│   │   ├── validators.py                # Email regex + sanitizers (length, html-escape)
│   │   ├── types.py                     # TypedDicts compartidos (Event, Context, Response)
│   │   ├── cache/                       # Sistema de cache con DynamoDB TTL (reusable)
│   │   │   ├── __init__.py              # Exports: DynamoDBCache, cached, CacheStatus
│   │   │   ├── client.py                # class DynamoDBCache (get/set/delete/invalidate/lock)
│   │   │   ├── decorator.py             # @cached(ttl, namespace, stale_for, tags)
│   │   │   ├── swr.py                   # Stale-while-revalidate: fresh|stale|expired states
│   │   │   ├── stampede.py              # Lock distribuido + XFetch probabilistic refresh
│   │   │   ├── invalidation.py          # Tag-based bulk invalidation (Scan + UpdateItem)
│   │   │   ├── serializers.py           # JSON + bytes_b64 fallback (Pydantic)
│   │   │   ├── types.py                 # TypedDicts: CacheEntry, CacheKey, CacheStatus
│   │   │   └── README.md                # Quick start + patterns + cuando usar SWR vs sync
│   │   └── rate_limit/                  # Rate-limit per-IP con DynamoDB (alternativa $0 a WAF)
│   │       ├── __init__.py              # Exports: check_or_raise, RateLimitExceededError
│   │       ├── check.py                 # API principal check_or_raise(ip, endpoint, country, turnstile_validated)
│   │       ├── rules.py                 # Lee rate_limit_rules table (cached via common.cache TTL 60s)
│   │       ├── buckets.py               # Sliding window weighted + atomic INCREMENT en rate_limit_buckets
│   │       ├── auto_blacklist.py        # Bot detection: 3+ tokens Turnstile validos en 60s -> blacklist 24h
│   │       ├── decisions.py             # TypedDict Decision(allowed, reason, retry_after, status_code)
│   │       ├── exceptions.py            # RateLimitExceededError, IPBlacklistedError, CountryBlockedError
│   │       └── README.md                # Algoritmo + integracion en handlers
│   │
│   ├── contact_form/                    # Lambda 1: POST /contact
│   │   ├── __init__.py
│   │   ├── handler.py                   # def lambda_handler(event, context)
│   │   ├── service.py                   # Logica de negocio (valida turnstile, persiste, envia email)
│   │   ├── schemas.py                   # JSON Schema input + Pydantic models output
│   │   ├── turnstile.py                 # Validacion del token contra siteverify
│   │   ├── persistence.py               # save_contact(payload) -> contact_id
│   │   ├── notification.py              # send_owner_email(contact)
│   │   ├── templates/
│   │   │   ├── owner_email.html.mjml   # Source MJML (compilar a HTML)
│   │   │   ├── owner_email.html         # Output compilado (committed)
│   │   │   └── owner_email.txt          # Plain-text fallback
│   │   └── requirements.txt             # Powertools + httpx + pydantic + boto3 (boto3 viene del runtime)
│   │
│   ├── tracking_pixel/                  # Lambda 2: POST /track
│   │   ├── __init__.py
│   │   ├── handler.py
│   │   ├── service.py                   # Logica: enriquece con CF headers, persiste con TTL +60d
│   │   ├── schemas.py                   # JSON Schema del payload (UA, viewport, UTMs, etc.)
│   │   ├── persistence.py               # save_tracking_event(payload) con TTL
│   │   ├── enrichment.py                # CF-IPCountry, CF-Connecting-IP, parse User-Agent
│   │   └── requirements.txt
│   │
│   ├── turnstile_validator/             # Lambda 3: POST /validate-turnstile (interno)
│   │   ├── __init__.py
│   │   ├── handler.py                   # Endpoint dedicado para validar tokens (uso futuro)
│   │   ├── service.py                   # POST a challenges.cloudflare.com/turnstile/v0/siteverify
│   │   ├── schemas.py
│   │   └── requirements.txt
│   │
│   ├── stream_processor/                # Lambda 4: DynamoDB Streams -> Neon PG
│   │   ├── __init__.py
│   │   ├── handler.py                   # Procesa event['Records'][i] del Stream
│   │   ├── service.py                   # Parsea NewImage/OldImage, batch UPSERT a PG
│   │   ├── transformers.py              # DynamoDB Item dict -> PG row mapping (contacts/tracking)
│   │   ├── pg_writer.py                 # psycopg3 conn cached + UPSERT prepared statements
│   │   ├── retries.py                   # DLQ + idempotency key (event_id) para reprocessing
│   │   └── requirements.txt             # psycopg[binary]>=3.2 + powertools + boto3
│   │
│   ├── aggregator/                      # Lambda 5: EventBridge cron diario -> PG aggregates
│   │   ├── __init__.py
│   │   ├── handler.py                   # Scheduled trigger 03:00 UTC daily
│   │   ├── service.py                   # Compute daily metrics, refresh materialized views
│   │   ├── queries.py                   # SQL queries para agregar tracking_events
│   │   └── requirements.txt
│   │
│   └── layers/
│       ├── common_python/               # Lambda Layer compartido (Powertools + httpx)
│       │   ├── requirements.txt         # aws-lambda-powertools[all]>=3 + httpx + pydantic
│       │   └── README.md                # Como rebuildear el layer
│       └── postgres_python/             # Lambda Layer para Lambdas que tocan PG
│           ├── requirements.txt         # psycopg[binary]>=3.2 (compiled arm64)
│           └── README.md
│
├── migrations/                          # SQL migrations para Neon PostgreSQL
│   ├── 001_init_schema.sql              # CREATE TABLE contacts, tracking_events (partitioned)
│   ├── 001_init_schema.down.sql         # Rollback (DROP TABLE)
│   ├── 002_indexes.sql                  # GIN, BRIN, B-tree compuestos
│   ├── 003_materialized_views.sql       # mv_contacts_by_month_niche, etc.
│   ├── 004_aggregates_tables.sql        # tracking_daily_aggregates, daily_metrics
│   └── 005_pg_partman_setup.sql         # Auto-create partitions mensuales para tracking_events
│
├── events/                              # Sample events para sam local invoke
│   ├── contact_form_valid.json          # POST /contact con token Turnstile valido (mocked)
│   ├── contact_form_invalid_token.json
│   ├── contact_form_missing_email.json
│   ├── contact_form_throttled.json      # 429 path
│   ├── tracking_pixel_valid.json
│   ├── tracking_pixel_with_utm.json
│   ├── tracking_pixel_no_session.json
│   ├── turnstile_validator_internal.json
│   ├── stream_record_contact_insert.json    # Sample DynamoDB Streams record (INSERT contacts)
│   ├── stream_record_tracking_insert.json   # Sample Stream record (INSERT tracking)
│   ├── stream_record_tracking_remove.json   # TTL-driven REMOVE event
│   └── aggregator_scheduled.json            # Sample EventBridge scheduled event
│
├── tests/                               # pytest + moto (mock AWS) + responses (mock httpx)
│   ├── conftest.py                      # Fixtures globales (mock_dynamodb, mock_ses, mock_ssm)
│   ├── pytest.ini                       # Markers: unit, integration
│   │
│   ├── unit/                            # Path mirror de src/
│   │   ├── common/
│   │   │   ├── test_cors.py
│   │   │   ├── test_ip_extractor.py
│   │   │   ├── test_responses.py
│   │   │   ├── test_validators.py
│   │   │   └── test_ulid.py
│   │   ├── contact_form/
│   │   │   ├── test_handler.py
│   │   │   ├── test_service.py
│   │   │   ├── test_turnstile.py
│   │   │   ├── test_persistence.py
│   │   │   └── test_notification.py
│   │   ├── tracking_pixel/
│   │   │   ├── test_handler.py
│   │   │   ├── test_service.py
│   │   │   ├── test_enrichment.py
│   │   │   └── test_persistence.py
│   │   └── turnstile_validator/
│   │       ├── test_handler.py
│   │       └── test_service.py
│   │
│   └── integration/                     # E2E contra sam local start-api + moto
│       ├── test_contact_flow.py         # POST /contact -> DynamoDB write + SES send
│       ├── test_tracking_flow.py        # POST /track -> DynamoDB write con TTL
│       └── test_throttle_flow.py        # 4 req rapidos a /contact -> 429 al 4to
│
├── scripts/                             # Helpers de operacion (no son Lambdas)
│   ├── setup_ssm.sh                     # Crea SSM Parameters con KMS para Turnstile secret
│   ├── verify_ses_dns.sh                # dig CNAMEs DKIM + TXT SPF/DMARC contra Cloudflare
│   ├── request_ses_production.md       # Plantilla del ticket de production access
│   ├── compile_mjml.mjs                 # Compila *.mjml a *.html (Node script, opt-in)
│   ├── tail_logs.sh                     # sam logs --tail por funcion (ergonomia)
│   ├── smoke_test.sh                    # curl contra el endpoint deployed
│   └── seed_test_contact.py             # Inserta contact de prueba en DynamoDB local
│
├── docs/                                # Documentacion especifica del backend
│   ├── api-contract.md                  # OpenAPI 3.1 inline del API Gateway
│   ├── data-model.md                    # Schema de las 2 tablas DynamoDB (contacts, tracking)
│   ├── secrets.md                       # Inventario de SSM Parameters + KMS keys
│   ├── monitoring.md                    # Dashboards, alarms, queries Logs Insights
│   ├── rate-limit-rules.md              # Esquema de rate_limit_rules + auto-blacklist patterns
│   ├── ses-setup.md                     # DKIM/SPF/DMARC records exactos para Cloudflare DNS
│   └── adr/                             # Architecture Decision Records
│       ├── 001-python-3.13-vs-3.14.md
│       ├── 002-rest-api-vs-http-api.md
│       ├── 003-dynamodb-rate-limit-no-waf.md     # Decision: self-managed rate-limit en lugar de WAF ($0 vs $7/mes)
│       ├── 004-on-demand-no-provisioned.md
│       ├── 005-two-tables-no-single-table.md
│       ├── 006-arm64-graviton2.md
│       ├── 007-snapstart-postpone.md
│       └── 008-managed-mode-turnstile.md
│
└── env/                                 # Variables de ambiente (NO committed los reales)
    ├── .env.example                     # Template con TODOS los keys requeridos
    ├── .env.dev                         # gitignored
    └── .env.prod                        # gitignored
```

---

## 2. Mapeo de archivos por responsabilidad

| Capa | Archivos clave | Que hace |
|------|----------------|----------|
| **IaC** | `template.yaml`, `samconfig.toml`, `Makefile` | Define recursos AWS, deploy reproducible, atajos |
| **Handler layer** | `src/<lambda>/handler.py` | Entry point Lambda (`lambda_handler(event, context)`) — solo orquesta, no logica |
| **Service layer** | `src/<lambda>/service.py` | Logica de negocio (combinar persistence + notification + validation) |
| **Persistence** | `src/<lambda>/persistence.py` | boto3 DynamoDB `put_item` con `ConditionExpression` |
| **Validation** | `src/<lambda>/schemas.py` + `src/common/validators.py` | JSON Schema (API GW) + Pydantic v2 (runtime) |
| **External APIs** | `src/contact_form/turnstile.py` | httpx POST a Cloudflare siteverify |
| **Shared layer** | `src/common/*.py` | Reutilizable entre 3 Lambdas (clients boto3 en module scope, types, helpers) |
| **Templates email** | `src/contact_form/templates/*.{mjml,html,txt}` | MJML source + HTML/TXT compilados |
| **Tests** | `tests/unit/<lambda>/test_*.py` | pytest path-mirroring + moto + responses |
| **Operations** | `scripts/*.sh`, `scripts/*.py` | Setup SSM, verify DNS, smoke tests |
| **ADRs** | `docs/adr/<N>-*.md` | Decision log con razones (no se borran nunca) |

---

## 3. Diagrama de flujo: form de contacto (POST /contact)

```
                       USUARIO en el browser
                              (Astro page en *.the-full-stack.com)
                              |
                              | 1. Cargar pagina
                              v
                       +----------------------+
                       |  ContactForm.astro   |
                       |  (packages/ui)       |
                       |  - sitekey publica   |
                       |  - widget Turnstile  |
                       +----------------------+
                              |
                              | 2. Usuario completa form
                              |    Turnstile genera token (TTL 5min)
                              v
                       +----------------------+
                       | fetch POST /contact  |
                       | body: {name, email,  |
                       |   message, service_  |
                       |   type, company,     |
                       |   role, budget,      |
                       |   timeline, cf_token}|
                       +----------------------+
                              |
                              | 3. HTTPS request
                              v
            ===================================================
            |             AWS CLOUD - us-west-2               |
            ===================================================
                              |
                              v
                       +----------------------+
                       |  Cloudflare upstream |   Capa 1: Defense edge (free)
                       |  DDoS L3/L4/L7       |   - Mitigation ilimitada
                       |  Bot Fight Mode      |   - Bloquea bots conocidos
                       |  CF-Connecting-IP    |   - Inyecta headers reales
                       +----------------------+
                              |
                              v
                       +----------------------+
                       |  API Gateway REST    |   Capa 2: Throttling global
                       |  POST /contact       |   - Burst 5, steady 1/s
                       |  CORS preflight OK   |   - Origenes whitelist
                       +----------------------+
                              |
                              v
                       +----------------------+
                       |  Request Validator   |   Capa 3: JSON Schema
                       |  - body shape OK?    |   - email format
                       |  - required fields?  |   - max length
                       |  - lengths OK?       |   - cf_token presente
                       +----------------------+
                              |
                  +-----------+-----------+
                  | Schema OK?            |
                  +-----------+-----------+
                  | YES                   | NO
                  v                       v
                  invoke                  +--------+
                                          | 400    |  Sin invocar Lambda
                                          +--------+  (ahorra costo)
                  |
                  v
                       +----------------------+
                       | Lambda: contact_form |
                       | Python 3.13, arm64   |   Capa 4: Business logic
                       | 512MB, 30s timeout   |
                       | @logger @tracer      |
                       +----------------------+
                              |
                              | 4a. Extrae IP real
                              |     CF-Connecting-IP > X-Forwarded-For
                              v
                       +----------------------+
                       | turnstile.py         |
                       | POST siteverify      |  ----+
                       | + idempotency_key    |      |
                       +----------------------+      |
                              |                      |  httpx call
                              v                      |
                       +-------------------+         |
                       | Cloudflare API    | <-------+
                       | challenges.       |
                       | cloudflare.com    |
                       | /turnstile/v0/    |
                       | siteverify        |
                       +-------------------+
                              |
                              v
                       Response JSON:
                       { success, hostname,
                         challenge_ts,
                         error-codes }
                              |
                              v
                       Verifica:
                       - success == true
                       - hostname IN whitelist (6 subdominios)
                       - challenge_ts < 5min antiguo
                              |
                  +-----------+-----------+
                  | Token valido?         |
                  +-----------+-----------+
                  | YES                   | NO
                  v                       v
                  continua            +-------------------------------+
                                      | logger.warning + metric BotBlocked|
                                      | return 403 Forbidden          |
                                      +-------------------------------+
                  |
                  v
                       +----------------------+
                       | persistence.py       |
                       | dynamodb.Table       |
                       | ('contacts')         |
                       | .put_item(           |
                       |   Item={             |
                       |     id: <uuidv7>,    |
                       |     email, name,     |
                       |     message,         |
                       |     service_type,    |
                       |     company, role,   |
                       |     budget, timeline,|
                       |     ip, country, ua, |
                       |     source_url,      |
                       |     created_at       |
                       |   },                 |
                       |   ConditionExpression|
                       |   = attribute_not_   |
                       |     exists(id)       |
                       | )                    |
                       +----------------------+
                              |
                              v
                       +----------------------+
                       | DynamoDB: contacts   |   Persistencia
                       | On-Demand            |   ~$0/mes (free tier)
                       | PK: id (UUIDv7)      |
                       | No TTL (retain all)  |
                       +----------------------+
                              |
                              | 4b. Si write OK -> notification
                              v
                       +----------------------+
                       | notification.py      |
                       | ses.send_email()     |
                       | - From: no-reply@... |
                       | - To: owner email    |
                       | - Subject: "Nuevo    |
                       |   contacto: <name>"  |
                       | - Body: HTML + TEXT  |
                       | - Multipart          |
                       +----------------------+
                              |
                              v
                       +----------------------+
                       | AWS SES v2           |   Email send
                       | DKIM signed          |   ~$0/mes (free 62k)
                       | SPF + DMARC valid    |
                       | Configuration Set    |
                       +----------------------+
                              |
                              | 4c. Event Destination
                              v
                       +----------------------+
                       | SNS Topic            |   Bounces / complaints
                       | (notifications)      |   -> SES handler Lambda
                       +----------------------+   (futuro, no MVP)
                              |
                              v
                       Owner inbox
                       (Gmail o el que sea)
                              |
                              |
                  <--- Response ---
                              |
                              v
                       +----------------------+
                       | 200 OK               |
                       | { ok: true,          |
                       |   contact_id: <id>,  |
                       |   message: "Gracias" }
                       +----------------------+
                              |
                              v
                       Frontend muestra
                       "Gracias, te respondo
                        en 24-48h"
                       + turnstile.reset()
                       + form.reset()

CAPA 5 transversal: CloudWatch Logs + X-Ray traces + Alarms
  - Cada step emite logs estructurados JSON (Powertools @logger)
  - X-Ray traza el path completo (API GW -> Lambda -> DynamoDB -> SES -> CF)
  - Alarm si ThrottledRequests > 10 en 5min (posible ataque)
  - Alarm si 5XXError > 1 en 5min (Lambda crash)
```

---

## 4. Diagrama de flujo: tracking pixel (POST /track)

```
            USUARIO renderiza pagina
                    (cualquier *.the-full-stack.com)
                    |
                    | 1. Astro render
                    v
            +----------------------+
            | TrackingPixel.astro  |
            | (packages/ui)        |
            | client:idle          |
            +----------------------+
                    |
                    | 2. document onLoad
                    v
            +----------------------+
            | Read consent cookie  |
            | (GDPR opt-in)        |
            +----------------------+
                    |
            +-------+-------+
            | Consent given?|
            +-------+-------+
            | YES           | NO
            v               v
        continua        SKIP (no track)
                            |
                            v
                        +--------+
                        | exit   |
                        +--------+
            |
            v
            +----------------------+
            | Collect signals      |
            | - navigator.userAgent|
            | - location.href      |
            | - document.referrer  |
            | - URLSearchParams    |
            |   (utm_source/...)   |
            | - screen.width/height|
            | - window.inner*      |
            | - navigator.language |
            | - Intl.DateTimeFormat|
            |   .resolvedOptions() |
            |   .timeZone          |
            | - sessionId (cookie  |
            |   set if missing,    |
            |   TTL session, opt-in|
            +----------------------+
                    |
                    | 3. Invisible Turnstile token (opt-in)
                    v
            +----------------------+
            | fetch POST /track    |
            | body: { ...signals,  |
            |   cf_token (invisible|
            |     mode token) }    |
            | mode: 'no-cors' OK   |
            |   o credentials:omit |
            +----------------------+
                    |
                    | 4. HTTPS request
                    v
        ===================================================
        |             AWS CLOUD - us-west-2               |
        ===================================================
                    |
                    v
            +----------------------+
            |  Cloudflare upstream |   Capa 1 (free)
            |  DDoS + Bot Fight    |
            +----------------------+
                    |
                    v
            +----------------------+
            |  API Gateway REST    |   Capa 2
            |  POST /track         |   Burst 60, steady 1/s
            |  CORS whitelist      |
            +----------------------+
                    |
                    v
            +----------------------+
            |  Request Validator   |   Capa 3
            |  - session_id format |
            |  - max payload size  |
            +----------------------+
                    |
                    v
            +----------------------+
            | Lambda:              |
            | tracking_pixel       |   Capa 4
            | Python 3.13, arm64   |
            | 256MB, 10s timeout   |
            +----------------------+
                    |
                    | 5a. Lee headers que CF inyecta
                    v
            +----------------------+
            | enrichment.py        |
            | - CF-Connecting-IP   |
            | - CF-IPCountry       |
            | - X-Forwarded-For    |
            | - User-Agent parse   |
            |   (device, browser)  |
            +----------------------+
                    |
                    | 5b. Calcula TTL
                    v
            +----------------------+
            | expires_at =         |
            |   int(time.time()) + |
            |   60 * 24 * 3600     |   (60 dias)
            +----------------------+
                    |
                    v
            +----------------------+
            | persistence.py       |
            | dynamodb.Table       |
            | ('tracking')         |
            | .put_item(Item={...})|
            +----------------------+
                    |
                    v
            +----------------------+
            | DynamoDB: tracking   |
            | On-Demand            |
            | PK: session_id       |
            | SK: page_id (UUIDv7) |   Sort por tiempo natural
            | TTL: expires_at      |   AWS borra a los 60d, 0 WCU
            +----------------------+
                    |
                    v
            +----------------------+
            | Response             |
            | 204 No Content       |   No payload, no parsing
            | + CORS headers       |   client friendly
            +----------------------+
                    |
                    v
            Browser ignora (no UX impact)

PERIODICO (no implementado MVP, futuro):
  - Cron Lambda lee tracking + agrega -> CloudWatch dashboard
  - O direct query desde un dashboard Astro stub

CAPA 5 transversal: CloudWatch Logs + X-Ray (mismo que contact form)
```

---

## 4.5. Diagrama de flujo: DynamoDB Streams -> Neon PG (stream_processor)

```
            DynamoDB tabla `contacts` o `tracking`
                    |
                    | 1. INSERT / MODIFY / REMOVE
                    v
            +----------------------+
            | DynamoDB Streams     |
            | StreamViewType:      |
            |   NEW_AND_OLD_IMAGES |
            | Retention: 24h       |
            +----------------------+
                    |
                    | 2. Event records (~5-30s lag)
                    |    Batch: maxBatchingWindow=10s,
                    |           batchSize=100
                    v
            +----------------------+
            | Lambda:              |
            | stream_processor     |   Python 3.13 arm64
            | 512MB, 60s timeout   |   Layer: postgres_python (psycopg3)
            | Reserved concurrency:|
            |   2 (proteger PG)    |
            +----------------------+
                    |
                    | 3. Por cada record en event['Records']:
                    v
            +----------------------+
            | transformers.py      |
            | DynamoDB Item        |
            |   {"id": "S": "...", | -> {"id": "...",
            |    "email": "S":...} |     "email": "..."}
            +----------------------+
                    |
                    | 4. Idempotency check
                    v
            +----------------------+
            | retries.py           |
            | event_id = record    |
            |   ['eventID']        |
            | Skip si ya procesado |
            |   (table: processed_ |
            |    stream_events)    |
            +----------------------+
                    |
                    v
            +----------------------+
            | pg_writer.py         |
            | psycopg3 conn cached |
            | UPSERT prepared      |
            | statement:           |
            |   INSERT ... ON      |
            |   CONFLICT(id) DO    |
            |   UPDATE SET ...     |
            +----------------------+
                    |
                    v
            +----------------------+
            | Neon PostgreSQL 18   |
            | tablas:              |
            |   - contacts         |   (CRM-style queries)
            |   - tracking_events  |   (row-level, particionado)
            +----------------------+
                    |
                    v
            +----------------------+
            | Mark event_id como   |
            | procesado (audit)    |
            +----------------------+
                    |
            +-------+-------+
            | Batch OK?     |
            +-------+-------+
            | YES           | NO (excepcion)
            v               v
        return OK       +----------------------+
                        | Reject batch         |
                        | (Lambda retries x3   |
                        |  con exp backoff)    |
                        +----------------------+
                                |
                                | Despues de 3 fallos:
                                v
                        +----------------------+
                        | DLQ (SQS)            |
                        | StreamProcessorDLQ   |
                        | CloudWatch Alarm     |
                        |   ApproximateNumber  |
                        |   OfMessages > 0     |
                        +----------------------+

CAPACIDAD:
  - DynamoDB Streams: 2 shards (auto-scaled), max 1000 writes/s por shard
  - Lambda concurrency reserved: 2 (no satura conn pool de Neon)
  - Neon: 1 connection del Lambda (psycopg3 cached en module scope)
  - Lag esperado: 5-30s entre write a Dynamo y read en PG
```

## 4.6. Diagrama de flujo: aggregator (EventBridge cron diario)

```
            EventBridge Scheduled Rule
                    "cron(0 3 * * ? *)"
                    (todos los dias 03:00 UTC)
                    |
                    | 1. Scheduled trigger
                    v
            +----------------------+
            | Lambda:              |
            | aggregator           |   Python 3.13 arm64
            | 1024MB, 5min timeout |   Layer: postgres_python
            +----------------------+
                    |
                    | 2. Calcula rango temporal
                    |    yesterday = today - 1 day
                    v
            +----------------------+
            | queries.py           |
            | Multiple SQL queries |
            | sobre tracking_events|
            +----------------------+
                    |
                    | 3a. Daily aggregates por (date, page, utm)
                    v
            +----------------------+
            | INSERT INTO          |
            | tracking_daily_      |
            | aggregates           |   (PK: date+page+utm_source)
            | SELECT               |
            |   date_trunc('day',  |
            |     created_at),     |
            |   path,              |
            |   utm_source,        |
            |   COUNT(*),          |
            |   COUNT(DISTINCT     |
            |     session_id),     |
            |   COUNT(DISTINCT ip) |
            | FROM tracking_events |
            | WHERE created_at >=  |
            |   yesterday          |
            | GROUP BY 1,2,3       |
            | ON CONFLICT DO UPDATE|
            +----------------------+
                    |
                    | 3b. Daily metrics (1 row/dia con KPIs)
                    v
            +----------------------+
            | INSERT INTO          |
            | daily_metrics        |   (PK: date)
            | SELECT               |
            |   date,              |
            |   total_pageviews,   |
            |   unique_sessions,   |
            |   total_contacts,    |
            |   conversion_rate,   |
            |   bounce_rate,       |
            |   avg_session_dur,   |
            |   top_landing_page,  |
            |   top_utm_source     |
            | FROM ...             |
            +----------------------+
                    |
                    | 3c. Refresh materialized views
                    v
            +----------------------+
            | REFRESH MATERIALIZED |
            | VIEW CONCURRENTLY    |
            |   mv_contacts_by_    |
            |     month_niche;     |
            | REFRESH MATERIALIZED |
            | VIEW CONCURRENTLY    |
            |   mv_session_journey;|
            +----------------------+
                    |
                    | 4. Drop partitions viejas (>60d)
                    v
            +----------------------+
            | SELECT               |
            |   partman.run_       |
            |   maintenance_proc();|
            | (pg_partman          |
            |  auto-creates next   |
            |  month partition +   |
            |  drops > retention)  |
            +----------------------+
                    |
                    v
            +----------------------+
            | logger.metric        |
            | AggregationDuration  |
            | AggregationRows      |
            | -> CloudWatch        |
            +----------------------+

OBSERVABILIDAD:
  - X-Ray trace: Lambda -> psycopg3 -> Neon (cada query como segment)
  - CloudWatch Alarm: AggregatorErrors >= 1 en 24h -> SNS owner
  - CloudWatch Alarm: AggregatorDuration > 4min (caso degradacion) -> SNS

POR QUE 03:00 UTC:
  - Hora de bajo trafico (LATAM dormida, EU empezando)
  - Permite ETL de las ultimas 24h de eventos
  - Neon scale-up automatico al cron, scale-to-zero despues
```

## 4.7. Arquitectura completa hibrida (overview)

```
                       BROWSER (Astro page)
                              |
        +---------------------+--------------------+
        |                                          |
        v                                          v
   POST /contact                              POST /track
        |                                          |
        v                                          v
   +-------------+                          +-------------+
   | Cloudflare  |                          | Cloudflare  |
   | DDoS+Bot    |                          | DDoS+Bot    |
   | (free)      |                          | (free)      |
   +-------------+                          +-------------+
        |                                          |
        v                                          v
   +-------------+                          +-------------+
   | API GW REST |                          | API GW REST |
   | + JSON      |                          | + JSON      |
   | validator   |                          | validator   |
   +-------------+                          +-------------+
        |                                          |
        v                                          v
   +-------------+                          +-------------+
   | Lambda:     |                          | Lambda:     |
   | contact_form|                          | tracking_   |
   | reserved=5  |                          | pixel       |
   | 1. Turnstile|                          | reserved=20 |
   | 2. Rate-    |                          | 1. Rate-    |
   |    limit MW |                          |    limit MW |
   | 3. Persist  |                          | 2. Enrich CF|
   +------+------+                          +------+------+
          |                                        |
          | put_item                               | put_item
          v                                        v
   +-------------+    +-------------+      +-------------+
   |  DynamoDB   |    |   AWS SES   |      |  DynamoDB   |
   |  contacts   |    | send_email  |      |  tracking   |
   |  (PK: id)   |    | (owner@..)  |      |  TTL +60d   |
   +------+------+    +-------------+      +------+------+
          |                                       |
          | Stream INSERT                         | Stream INSERT/REMOVE
          v                                       v
   +---------------------------------------------------+
   |                DynamoDB Streams                   |
   |          (NEW_AND_OLD_IMAGES, 24h retention)      |
   +---------------------------+-----------------------+
                               |
                               | batch (size=100, window=10s)
                               v
                       +-----------------+
                       | Lambda:         |
                       | stream_processor|
                       | (reserved=2)    |
                       | psycopg3 cached |
                       +--------+--------+
                                |
                                | UPSERT batch
                                v
                       +-----------------+
                       |  Neon PG 18     |
                       |  (us-west-2)    |
                       |  Free tier:     |
                       |   0.5GB +       |
                       |   192h compute  |
                       |  Scale to zero  |
                       +--------+--------+
                                ^
                                |
                                | refresh materialized views
                                | + insert daily_metrics
                                |
                       +--------+--------+
                       | Lambda:         |
                       | aggregator      |  <----- EventBridge
                       | (cron 03:00 UTC)|         daily schedule
                       +-----------------+

TABLAS EN Neon PG:
  - contacts (normalizada con CHECK + GIN to_tsvector)
  - tracking_events (range partitioned por mes via pg_partman)
  - tracking_daily_aggregates (PK: date+page+utm_source)
  - daily_metrics (1 row/dia, KPIs derivados)
  - mv_contacts_by_month_niche (materialized view)
  - mv_session_journey (materialized view, LAG/LEAD)
  - processed_stream_events (idempotency log)

QUE VIVE DONDE:
  +--------------------------+-----------+---------+
  | Workload                 | DynamoDB  | Neon PG |
  +--------------------------+-----------+---------+
  | Lambda writes (hot path) | YES       | NO      |
  | Form submission save     | source    | replica |
  | Tracking pixel save      | source    | replica |
  | TTL auto-delete tracking | YES (60d) | drop    |
  |                          |           | partition
  | Owner CRM queries        | NO        | YES     |
  | Window funcs / LAG/LEAD  | NO        | YES     |
  | Joins entre tablas       | NO        | YES     |
  | Full-text search msg     | NO        | YES GIN |
  | Daily KPIs dashboard     | NO        | YES     |
  | Session journey          | NO        | YES MV  |
  +--------------------------+-----------+---------+

LATENCIA HOT PATH (form submit -> response):
  ~300-500ms warm, ~800ms cold (Turnstile siteverify domina)

LATENCIA STREAM REPLICA (DynamoDB write -> visible en PG):
  5-30s tipico, max 60s (DLQ si excede)
```

## 4.8. Diagrama de flujo: cache module (src/common/cache/)

Sistema de cache de proposito general con DynamoDB TTL. Cualquier Lambda
del modulo (contact-form, tracking-pixel, turnstile-validator,
stream-processor, aggregator) puede usarlo via import desde
`src/common/cache/`. Detalle en
`.claude/docs/dynamodb-cache/` (8 docs) + skill `dynamodb-cache`.

```
            Cualquier Lambda Python 3.13
                    |
                    | from common.cache import cached, DynamoDBCache
                    v
            +----------------------+
            | @cached(             |
            |   ttl=300,           |   5 min fresh
            |   stale_for=600,     |   10 min stale (SWR)
            |   namespace='ssm',   |
            |   tags=['secrets']   |
            | )                    |
            | def get_turnstile_   |
            |   secret() -> str:   |
            |   ...                |
            +----------------------+
                    |
                    | 1. Invocacion
                    v
            +----------------------+
            | hash key = sha256(   |
            |   namespace +        |
            |   fn.__name__ +      |
            |   args + kwargs)     |
            +----------------------+
                    |
                    v
            +----------------------+
            | DynamoDBCache.get()  |   GetItem en tabla `cache`
            +----------------------+
                    |
            +-------+-------+
            | Estado?       |
            +---------------+
            |
            | fresh (now < expires_at)
            |   -> return cached value (HIT)
            |
            | stale (expires_at < now < stale_until)
            |   -> return cached value + fire-and-forget refresh
            |     +------------------------+
            |     | asyncio.create_task(   |
            |     |   _refresh_async(...)) |
            |     +------------------------+
            |
            | expired (now >= stale_until)  o miss (no item)
            |   v
            |   +----------------------+
            |   | acquire_lock()       |   ConditionalWrite:
            |   | UpdateItem           |   attribute_not_exists(lock_owner)
            |   |   ConditionExpression|   OR lock_expires < now
            |   +----------------------+
            |       |
            |   +---+---+
            |   | OK?   |
            |   +---+---+
            |   |       |
            |   | YES   | NO (otro Lambda tiene el lock)
            |   v       v
            |   compute   busy-wait (max 500ms, then return stale)
            |   |
            |   v
            |   +----------------------+
            |   | result = fn(...)     |   Logica del usuario:
            |   |                      |   - boto3 ssm.get_parameter()
            |   |                      |   - httpx siteverify
            |   |                      |   - psycopg3 SELECT
            |   +----------------------+
            |       |
            |       v
            |   +----------------------+
            |   | DynamoDBCache.set()  |   PutItem:
            |   |   key, value,        |     - value (JSON-serialized)
            |   |   ttl, tags          |     - expires_at = now + ttl
            |   |                      |     - stale_until = now + ttl + stale_for
            |   |                      |     - tags (SS)
            |   |                      |     - release lock
            |   +----------------------+
            |       |
            |       v
            |   +----------------------+
            |   | Return result        |
            |   +----------------------+
            |
            v
        Caller recibe valor (cached o fresh)

TABLA cache (single-table design):
+-------------------------------+
| PK (HASH): cache_key          |  ej. "ssm:get_turnstile_secret:<hash>"
+-------------------------------+
| value          (S)            |  JSON serialized
| value_type     (S)            |  'string'|'json'|'bytes_b64'
| created_at     (S, ISO8601)   |
| expires_at     (N, epoch)     |  -> TTL attribute (AWS auto-delete)
| stale_until    (N, epoch)     |  SWR window end
| tags           (SS, optional) |  bulk invalidation por tag
| lock_owner     (S, optional)  |  Lambda request_id que tiene el lock
| lock_expires   (N, optional)  |  Lock TTL (15s tipico)
+-------------------------------+

CACHE STAMPEDE PREVENTION:
  1. Lock distribuido: solo 1 Lambda recompute por key/ventana
  2. XFetch probabilistic: cada Lambda decide refrescar antes
     del TTL con prob = (-1 * delta * log(rand())) > (expires_at - now)
     -> evita stampede sincronizado al expirar
  3. Stale-while-revalidate: si llega stale, devuelve cached
     y refresca async (no blockea response)

INVALIDACION:
  - Por key:  cache.delete(key)
  - Por tag:  cache.invalidate(tag='secrets')
              -> Scan FilterExpression contains(tags, 'secrets')
              -> BatchUpdateItem expires_at = 0 (soft delete)
              -> TTL run elimina dentro de 48h

COSTO ESTIMADO (este portfolio):
  - ~1000 reads/min picos, ~100 writes/min
  - 25 RCU + 25 WCU free tier perpetuo
  - Tabla < 100MB (5GB free tier)
  - $0/mes total
```

### Que se cachea en este proyecto

| Use case | Lambda(s) | Namespace | TTL | stale_for | Tags |
|----------|-----------|-----------|-----|-----------|------|
| Turnstile secret (SSM) | contact-form, turnstile-validator | `ssm` | 300s | 600s | `[secrets]` |
| Neon connection URL (SSM) | stream-processor, aggregator | `ssm` | 300s | 600s | `[secrets]` |
| Owner email (SSM) | contact-form | `ssm` | 3600s | 7200s | `[config]` |
| Country lookups (IP -> country) | tracking-pixel | `geo` | 86400s | 172800s | `[geo]` |
| Daily metrics (Neon agg) | dashboard futuro | `pg-query` | 1800s | 3600s | `[analytics, daily]` |
| Top landing pages (Neon mv) | dashboard futuro | `pg-query` | 1800s | 3600s | `[analytics, mv]` |
| User-Agent parsed (UA -> device/browser) | tracking-pixel | `ua-parse` | 86400s | 172800s | `[parsing]` |

USO TIPICO en contact_form:

```python
from common.cache import cached

@cached(ttl=300, stale_for=600, namespace='ssm', tags=['secrets'])
def get_turnstile_secret() -> str:
    return ssm.get_parameter(
        Name='/portfolio/turnstile-secret',
        WithDecryption=True,
    )['Parameter']['Value']
```

Sin cache: cada invocacion del Lambda hace `ssm.get_parameter` (+30ms +
cost de SSM API). Con cache: warm Lambda lo lee de DynamoDB en ~5ms,
cold Lambda solo paga la primera invocacion.

INVALIDACION post-rotacion del secret:

```python
from common.cache import DynamoDBCache

cache = DynamoDBCache(table_name='cache')
cache.invalidate(tag='secrets')   # Borra todos los secrets cacheados
```

CUANDO NO USAR cache:

- Form submission (cada uno es unico, no cachear)
- Tracking event (idem)
- Stream processing (cada record es unico)
- Operaciones con side effects (writes a Dynamo/SES/PG)

## 4.9. Diagrama de flujo: rate-limit middleware (common/rate_limit/)

Reemplaza la funcionalidad de AWS WAF rate-based rules con un middleware
self-managed en cada Lambda. Costo: $0/mes (DynamoDB free tier perpetuo).
Detalle completo en `.claude/docs/serverless-rate-limit/` + skill
`serverless-rate-limit`.

```
            Lambda (contact_form o tracking_pixel)
                    |
                    | 1. Turnstile YA validado (capa anterior)
                    v
            +----------------------+
            | extract_ip(event)    |   Prioridad:
            |                      |   1. CF-Connecting-IP
            |                      |   2. X-Forwarded-For[0]
            |                      |   3. requestContext.identity
            +----------------------+
                    |
                    | 2. country = headers.get('CF-IPCountry', '')
                    v
            +----------------------+
            | check_or_raise(      |
            |   ip,                |
            |   endpoint,          |
            |   country,           |
            |   turnstile_         |
            |     validated=True   |
            | )                    |
            +----------------------+
                    |
                    | Step A: read rules (cached 60s)
                    v
            +----------------------+
            | rate_limit_rules     |
            | (cached via          |
            |  common/cache)       |
            |  - endpoint rule     |   limit + window_seconds
            |  - ip whitelist      |   skip rate-limit
            |  - ip blacklist      |   immediate 403
            |  - country rule      |   block/throttle por pais
            +----------------------+
                    |
            +-------+-------+
            | Decision?     |
            +-------+-------+
            |       |       |
            | IP    | IP    | continue
            | white | black |
            | -list | list  |
            v       v       v
        SKIP   +-------+   +------------+
        check  | 403   |   | country    |
               | inmed |   | rule check |
               +-------+   +------------+
                                |
                                v
            +----------------------+
            | Step B: sliding      |
            |  window weighted     |
            |                      |
            | now = time.time()    |
            | window_start =       |
            |   (now // ws) * ws   |
            | prev_start =         |
            |   window_start - ws  |
            +----------------------+
                    |
                    v
            +----------------------+
            | GetItem 2x batch:    |
            |   current bucket     |
            |   previous bucket    |
            +----------------------+
                    |
                    v
            +----------------------+
            | elapsed =            |
            |   now - window_start |
            | prev_weight =        |
            |   (ws - elapsed) / ws|
            | effective_count =    |
            |   current_count +    |
            |   (prev_count *      |
            |    prev_weight)      |
            +----------------------+
                    |
            +-------+-------+
            | effective_    |
            |  count >=     |
            |  limit?       |
            +-------+-------+
            |               |
            | YES (deny)    | NO (allow)
            v               v
        +-------+       +----------------------+
        | 429 + |       | Step C: atomic       |
        | Retry-|       |   increment          |
        | After |       |                      |
        +-------+       | UpdateItem ADD       |
                       |   count :one          |
                       |   turnstile_tokens    |
                       |     :one (si valido)  |
                       |                      |
                       | SET expires_at = if_  |
                       |   not_exists(...)     |
                       +----------------------+
                                |
                                v
                       +----------------------+
                       | Step D: auto-        |
                       |   blacklist check    |
                       |                      |
                       | IF turnstile_tokens  |
                       |   >= 3 AND           |
                       |   window <= 60s:     |
                       |                      |
                       |   PUT rate_limit_    |
                       |    rules             |
                       |     rule_key:        |
                       |       "ip#<addr>"    |
                       |     kind: blacklist  |
                       |     expires_at:      |
                       |       now + 86400    |
                       |     reason: "auto"   |
                       |                      |
                       |   logger.warning     |
                       |   metric Auto        |
                       |     Blacklist        |
                       |     Triggered        |
                       +----------------------+
                                |
                                v
                       +----------------------+
                       | Continue handler:    |
                       |   persist contact    |
                       |   send email SES     |
                       +----------------------+

CARACTERISTICAS:
  - Atomic: DynamoDB UpdateItem ADD es atomic, sin race conditions
  - No lock distribuido necesario (a diferencia de cache)
  - TTL nativo elimina buckets viejos a costo 0
  - Cache de rules (60s) reduce reads en hot path
  - Defensa en profundidad:
      Layer 0: Cloudflare DDoS edge (free)
      Layer 1: Middleware rate-limit (este)
      Layer 1.5: Reserved concurrency Lambda (defensa pasiva)
      Layer 2: API Gateway throttle global
      Layer 3: Request validator JSON Schema
      Layer 4: Business logic (Turnstile validation)
      Layer 5: CloudWatch alarms + auto-blacklist

COSTO:
  - 0 WCU/RCU consumidos (free tier 25 + 25 perpetuos cubren todo)
  - ~30k items vivos en buckets (free tier 25GB storage)
  - Total: $0/mes vs $7/mes WAF
```

### Que se rate-limita

| Endpoint | Limit | Window | Action | Endpoint rule_key |
|----------|-------|--------|--------|-------------------|
| POST /contact | 3 | 300s | throttle (429) | `endpoint#/contact` |
| POST /track | 30 | 300s | throttle (429) | `endpoint#/track` |
| POST /validate-turnstile | 5 | 60s | throttle (429) | `endpoint#/validate-turnstile` |
| Default (sin regla explicita) | 10 | 60s | throttle | `endpoint#*` (fallback) |

### Que se cachea

- `rate_limit_rules` con `@cached(ttl=60, stale_for=300, namespace='rate-rules')` — reduce GetItem en hot path
- Buckets NO se cachean (counter atomic, debe ser fresh)

## 5. Diagrama de capas (defense in depth)

```
+---------------------------------------------------------------+
|  Layer 5: Observability (transversal)                         |
|    CloudWatch Logs + X-Ray Traces + Alarms + SNS              |
+---------------------------------------------------------------+
              ^                                ^
              |                                |
+-------------+---------+        +-------------+---------------+
|                                                              |
|  Layer 4: Business Logic                                     |
|    Lambda Python 3.13 (Powertools, httpx, boto3)             |
|    - Validar Turnstile (server-to-server)                    |
|    - Validar dominio + freshness del token                   |
|    - Persistir en DynamoDB                                   |
|    - Enviar email via SES                                    |
+-------------+--------------------------------+---------------+
              ^                                |
              |                                |
+-------------+---------+        +-------------+---------------+
|                                                              |
|  Layer 3: Request Validation                                 |
|    API Gateway Models + JSON Schema                          |
|    - Body shape, required fields, max lengths                |
|    - Rechaza con 400 ANTES de invocar Lambda                 |
+-------------+--------------------------------+---------------+
              ^                                |
              |                                |
+-------------+---------+        +-------------+---------------+
|                                                              |
|  Layer 2: API Gateway Throttling                             |
|    Method-level burst + steady rate                          |
|    - GLOBAL (no per-IP)                                      |
|    - Protege contra spikes generales                         |
|    - Devuelve 429 con Retry-After                            |
+-------------+--------------------------------+---------------+
              ^                                |
              |                                |
+-------------+---------+        +-------------+---------------+
|                                                              |
|  Layer 1.5: Lambda Reserved Concurrency                      |
|    contact_form max 5 concurrent invocations                 |
|    tracking_pixel max 20 concurrent invocations              |
|    AWS retorna 429 sin invocar Lambda si excede              |
|    (defensa pasiva contra DDoS volumetrico, costo $0)        |
+-------------+--------------------------------+---------------+
              ^                                |
              |                                |
+-------------+---------+        +-------------+---------------+
|                                                              |
|  Layer 1: Middleware rate-limit per-IP (DynamoDB)            |
|    Sliding window weighted en common/rate_limit/             |
|    - /contact: 3 req/5min/IP                                 |
|    - /track:   30 req/5min/IP                                |
|    - IP whitelist + blacklist + country rules                |
|    - Auto-blacklist si 3+ tokens validos en 60s              |
|    - Costo: $0 (free tier DynamoDB perpetuo)                 |
+-------------+--------------------------------+---------------+
              ^                                |
              |                                |
+-------------+---------+        +-------------+---------------+
|                                                              |
|  Layer 0: Cloudflare (upstream del cliente, FREE)            |
|    - DDoS L3/L4/L7 mitigation (free tier ilimitado)          |
|    - Bot Fight Mode (gratis)                                 |
|    - Inyecta CF-Connecting-IP, CF-IPCountry headers          |
|    - Turnstile widget cargado client-side                    |
+--------------------------------------------------------------+
              ^
              |
        Internet (browser)
```

---

## 6. Diagrama de datos: tablas DynamoDB

```
+-------------------------------+
|    Tabla: contacts            |
|    BillingMode: PAY_PER_REQUEST
|    PITR: Enabled              |
+-------------------------------+
| PK (HASH)    : id (S, UUIDv7) |
+-------------------------------+
| email           (S)           |
| name            (S)           |
| message         (S)           |
| service_type    (S)  enum     |  freelance | contract | part-time |
|                                  tech-lead | consulting | other
| company         (S, optional) |
| role            (S, optional) |
| budget          (S, optional) |
| timeline        (S, optional) |
| source_url      (S)           |  La pagina exacta del envio
| source_subdomain (S)          |  Cual de los 6 (hub/fintech/...)
| ip_address      (S)           |  CF-Connecting-IP
| country         (S, 2-char)   |  CF-IPCountry
| user_agent      (S)           |
| created_at      (S, ISO8601)  |
| turnstile_hostname (S)        |  Para audit
+-------------------------------+

+-------------------------------+
|    Tabla: tracking            |
|    BillingMode: PAY_PER_REQUEST
|    PITR: Disabled (data efimera)
|    TTL: expires_at            |
+-------------------------------+
| PK (HASH)    : session_id (S) |
| SK (RANGE)   : page_id    (S, UUIDv7)
+-------------------------------+
| url             (S)           |
| path            (S)           |
| referrer        (S, optional) |
| utm_source      (S, optional) |
| utm_medium      (S, optional) |
| utm_campaign    (S, optional) |
| utm_term        (S, optional) |
| utm_content     (S, optional) |
| screen_res      (S)  ej 1920x1080
| viewport        (S)  ej 1440x900
| device_type     (S)  desktop|mobile|tablet
| browser         (S)  parsed from UA
| os              (S)  parsed from UA
| lang            (S)  navigator.language
| timezone        (S)  Intl resolvedOptions
| ip_address      (S)
| country         (S, 2-char)
| user_agent      (S)
| source_subdomain (S)
| created_at      (S, ISO8601)
| expires_at      (N, Unix epoch seconds)  -> AUTO DELETE +60d
+-------------------------------+

+-------------------------------+
|    Tabla: rate_limit_rules    |
|    BillingMode: PAY_PER_REQUEST
|    SSE: enabled               |
|    TTL: expires_at (blacklist auto)
+-------------------------------+
| PK (HASH): rule_key (S)       |  patrones:
|                               |    "endpoint#/contact"
|                               |    "endpoint#/track"
|                               |    "endpoint#*" (default fallback)
|                               |    "ip#X.X.X.X" (white o blacklist)
|                               |    "country#XX" (ISO 3166-1 alpha-2)
+-------------------------------+
| kind            (S)           |  'endpoint' | 'ip_whitelist'
|                               |  'ip_blacklist' | 'country'
| limit           (N, optional) |  Max requests en window
| window_seconds  (N, optional) |  Tamano ventana (300 = 5min)
| action          (S)           |  'allow' | 'block' | 'throttle'
| expires_at      (N, optional) |  TTL para blacklist auto +24h
| reason          (S)           |  Texto descriptivo (audit)
| created_at      (S, ISO8601)  |
| created_by      (S)           |  'manual' | 'cli' | 'auto-detected'
+-------------------------------+

+-------------------------------+
|    Tabla: rate_limit_buckets  |
|    BillingMode: PAY_PER_REQUEST
|    TTL: expires_at (cleanup ventanas pasadas)
+-------------------------------+
| PK (HASH): bucket_key (S)     |  patron:
|                               |    "<ip>#<endpoint>#<window_start_epoch>"
|                               |  ej. "203.0.113.42#/contact#1715688600"
+-------------------------------+
| count           (N)           |  Atomic counter (UpdateItem ADD)
| window_start    (N, epoch)    |  Inicio de la ventana
| window_seconds  (N)           |  Duracion (300 = 5min)
| first_request   (S, ISO8601)  |  Primera request del bucket
| last_request    (S, ISO8601)  |  Ultima request
| turnstile_tokens (N)          |  Counter de tokens validos (bot detection)
| expires_at      (N, epoch)    |  window_start + window_seconds + 60s grace
+-------------------------------+
```

## 6.5. Diagrama de datos: tablas Neon PostgreSQL 18

Replicado desde DynamoDB Streams + agregado por aggregator cron. Las
tablas en PG son normalizadas, tipadas y con CHECK constraints. Ver
detalle completo en `.claude/docs/postgresql-18-analytics/02-schema-design-this-project.md`.

```
+--------------------------------------------+
|  Tabla: contacts                           |
|  (normalizada para CRM-style queries)      |
+--------------------------------------------+
| id              UUID PRIMARY KEY (UUIDv7)  |
| email           CITEXT NOT NULL            |  CITEXT = case-insensitive
| name            TEXT NOT NULL              |
| message         TEXT NOT NULL              |  -> GIN to_tsvector('spanish')
| service_type    TEXT NOT NULL              |  CHECK in enum
|                                            |  ('freelance','contract',
|                                            |   'part-time','tech-lead',
|                                            |   'consulting','other')
| company         TEXT                       |
| role            TEXT                       |
| budget          TEXT                       |
| timeline        TEXT                       |
| source_url      TEXT NOT NULL              |
| source_subdomain TEXT NOT NULL             |  enum 6 niches
| ip_address      INET NOT NULL              |  PG native IPv4/IPv6
| country         CHAR(2)                    |  ISO 3166-1 alpha-2
| user_agent      TEXT NOT NULL              |
| turnstile_hostname TEXT NOT NULL           |
| metadata        JSONB                      |  -> GIN jsonb_path_ops
| created_at      TIMESTAMPTZ NOT NULL       |
| stream_event_id TEXT NOT NULL UNIQUE       |  Idempotency desde DynamoDB Streams
+--------------------------------------------+

+--------------------------------------------+
|  Tabla: tracking_events                    |
|  (range partitioned por mes via pg_partman)|
+--------------------------------------------+
| session_id      UUID NOT NULL              |  PK part
| page_id         UUID NOT NULL              |  PK part (UUIDv7 -> sort time)
| url             TEXT NOT NULL              |
| path            TEXT NOT NULL              |
| referrer        TEXT                       |
| utm_source      TEXT                       |
| utm_medium      TEXT                       |
| utm_campaign    TEXT                       |
| utm_term        TEXT                       |
| utm_content     TEXT                       |
| screen_res      TEXT                       |
| viewport        TEXT                       |
| device_type     TEXT CHECK in              |  ('desktop','mobile','tablet')
| browser         TEXT                       |
| os              TEXT                       |
| lang            TEXT                       |
| timezone        TEXT                       |
| ip_address      INET                       |
| country         CHAR(2)                    |
| user_agent      TEXT                       |
| source_subdomain TEXT NOT NULL             |
| extra           JSONB                      |  -> GIN jsonb_path_ops
| created_at      TIMESTAMPTZ NOT NULL       |  PARTITION KEY
| expires_at      TIMESTAMPTZ NOT NULL       |  +60d (drop partition mensual)
| stream_event_id TEXT NOT NULL UNIQUE       |
| PRIMARY KEY (session_id, page_id, created_at)
+--------------------------------------------+

Partitions (auto-creadas por pg_partman):
  - tracking_events_2026_05 (mayo 2026)
  - tracking_events_2026_06 (junio 2026)
  - ... (1 partition por mes)
  - Drop automatico despues de 60d

+--------------------------------------------+
|  Tabla: tracking_daily_aggregates          |
|  (computada por aggregator Lambda diario)  |
+--------------------------------------------+
| date            DATE NOT NULL              |  PK part
| path            TEXT NOT NULL              |  PK part
| utm_source      TEXT NOT NULL DEFAULT ''   |  PK part
| pageviews       INTEGER NOT NULL           |
| unique_sessions INTEGER NOT NULL           |
| unique_ips      INTEGER NOT NULL           |
| countries       INTEGER NOT NULL           |
| device_breakdown JSONB                     |  {desktop:N, mobile:N, tablet:N}
| computed_at     TIMESTAMPTZ NOT NULL       |
| PRIMARY KEY (date, path, utm_source)       |
+--------------------------------------------+

+--------------------------------------------+
|  Tabla: daily_metrics                      |
|  (1 row por dia con KPIs derivados)        |
+--------------------------------------------+
| date            DATE PRIMARY KEY           |
| total_pageviews    INTEGER                 |
| unique_sessions    INTEGER                 |
| total_contacts     INTEGER                 |
| conversion_rate    NUMERIC(5,4)            |  contacts / sessions
| bounce_rate        NUMERIC(5,4)            |  sessions con 1 sola pagina
| avg_session_secs   INTEGER                 |
| top_landing_page   TEXT                    |
| top_utm_source     TEXT                    |
| top_country        CHAR(2)                 |
| computed_at        TIMESTAMPTZ             |
+--------------------------------------------+

+--------------------------------------------+
|  Tabla: processed_stream_events            |
|  (idempotency log del stream_processor)    |
+--------------------------------------------+
| event_id        TEXT PRIMARY KEY           |  DynamoDB record eventID
| source_table    TEXT NOT NULL              |  'contacts' | 'tracking'
| event_name      TEXT NOT NULL              |  INSERT|MODIFY|REMOVE
| processed_at    TIMESTAMPTZ NOT NULL       |
+--------------------------------------------+

Materialized views (refreshed por aggregator):
  - mv_contacts_by_month_niche
  - mv_session_journey (LAG/LEAD reconstruction)
  - mv_top_landing_pages
```

---

## 7. Diagrama del SAM template (resources high-level)

```
template.yaml (resources)
|
+-- AWS::Serverless::LayerVersion       CommonLayer
|     ContentUri: src/layers/common_python/
|     CompatibleRuntimes: [python3.13]
|     CompatibleArchitectures: [arm64]
|     # Powertools v3 + httpx + pydantic
|
+-- AWS::Serverless::LayerVersion       PostgresLayer
|     ContentUri: src/layers/postgres_python/
|     CompatibleRuntimes: [python3.13]
|     CompatibleArchitectures: [arm64]
|     # psycopg[binary]>=3.2 compiled for arm64
|
+-- AWS::Serverless::Function           ContactFormFunction
|     CodeUri: src/contact_form/
|     Runtime: python3.13
|     Architectures: [arm64]
|     MemorySize: 512
|     Timeout: 30
|     Tracing: Active
|     ReservedConcurrentExecutions: 5         # Defensa pasiva DDoS volumetrico
|     Layers: [!Ref CommonLayer]
|     Policies:
|       - DynamoDBWritePolicy: contacts
|       - DynamoDBReadPolicy: rate_limit_rules     # Lee endpoint/IP/country rules
|       - DynamoDBCrudPolicy: rate_limit_buckets   # Atomic increment counters + write auto-blacklist
|       - DynamoDBCrudPolicy: cache                # Cache de rules + SSM
|       - Statement (ses:SendEmail con condition FromAddress)
|       - Statement (ssm:GetParameter /portfolio/turnstile-secret)
|       - Statement (kms:Decrypt alias/portfolio-lambdas)
|     Events:
|       ContactPost:
|         Type: Api
|         RestApiId: !Ref PortfolioApi
|         Path: /contact
|         Method: POST
|
+-- AWS::Serverless::Function           TrackingPixelFunction
|     (similar, 256MB, tabla tracking)
|     ReservedConcurrentExecutions: 20         # Tracking acepta mas concurrency
|     Policies:
|       - DynamoDBWritePolicy: tracking
|       - DynamoDBReadPolicy: rate_limit_rules
|       - DynamoDBCrudPolicy: rate_limit_buckets
|       - DynamoDBCrudPolicy: cache
|
+-- AWS::Serverless::Function           TurnstileValidatorFunction
|     (similar, sin DynamoDB ni SES)
|
+-- AWS::Serverless::Function           StreamProcessorFunction
|     CodeUri: src/stream_processor/
|     Runtime: python3.13
|     Architectures: [arm64]
|     MemorySize: 512
|     Timeout: 60
|     ReservedConcurrentExecutions: 2     # Proteger Neon conn pool
|     Layers: [!Ref CommonLayer, !Ref PostgresLayer]
|     Environment:
|       Variables:
|         NEON_URL_PARAM: /portfolio/neon-url
|         CACHE_TABLE: !Ref CacheTable
|     Policies:
|       - Statement (ssm:GetParameter /portfolio/neon-url + kms:Decrypt)
|       - DynamoDBReadPolicy: cache (para invalidar PG-query tags)
|       - DynamoDBWritePolicy: cache
|     Events:
|       ContactsStream:
|         Type: DynamoDB
|         Properties:
|           Stream: !GetAtt ContactsTable.StreamArn
|           StartingPosition: TRIM_HORIZON
|           BatchSize: 100
|           MaximumBatchingWindowInSeconds: 10
|           MaximumRetryAttempts: 3
|           DestinationConfig:
|             OnFailure:
|               Destination: !GetAtt StreamProcessorDLQ.Arn
|       TrackingStream:
|         Type: DynamoDB
|         Properties:
|           Stream: !GetAtt TrackingTable.StreamArn
|           StartingPosition: TRIM_HORIZON
|           BatchSize: 100
|           MaximumBatchingWindowInSeconds: 10
|           MaximumRetryAttempts: 3
|           DestinationConfig:
|             OnFailure:
|               Destination: !GetAtt StreamProcessorDLQ.Arn
|
+-- AWS::Serverless::Function           AggregatorFunction
|     CodeUri: src/aggregator/
|     Runtime: python3.13
|     Architectures: [arm64]
|     MemorySize: 1024
|     Timeout: 300                          # 5 min para agregaciones diarias
|     Layers: [!Ref CommonLayer, !Ref PostgresLayer]
|     Environment:
|       Variables:
|         NEON_URL_PARAM: /portfolio/neon-url
|         CACHE_TABLE: !Ref CacheTable
|     Policies:
|       - Statement (ssm:GetParameter /portfolio/neon-url + kms:Decrypt)
|       - DynamoDBCrudPolicy: cache         # Invalida pg-query tags
|     Events:
|       DailySchedule:
|         Type: Schedule
|         Properties:
|           Schedule: cron(0 3 * * ? *)     # 03:00 UTC daily
|           Enabled: true
|
+-- AWS::SQS::Queue                     StreamProcessorDLQ
|     MessageRetentionPeriod: 1209600       # 14 dias
|     VisibilityTimeout: 60
|
+-- AWS::CloudWatch::Alarm              StreamDLQAlarm
|     MetricName: ApproximateNumberOfMessagesVisible
|     Namespace: AWS/SQS
|     Dimensions: [QueueName: !GetAtt StreamProcessorDLQ.QueueName]
|     Threshold: 1
|     AlarmActions: [!Ref AlertsTopic]
|
+-- AWS::Serverless::Api                PortfolioApi
|     EndpointConfiguration: REGIONAL
|     StageName: prod
|     Cors:
|       AllowOrigin: "'https://the-full-stack.com'"  (whitelist runtime
|         resolved con Gateway Responses para multi-domain via header
|         Origin echo seguro)
|       AllowMethods: "'POST,OPTIONS'"
|       AllowHeaders: "'Content-Type'"
|     MethodSettings:
|       - ResourcePath: /contact
|         HttpMethod: POST
|         ThrottlingBurstLimit: 5
|         ThrottlingRateLimit: 1
|       - ResourcePath: /track
|         HttpMethod: POST
|         ThrottlingBurstLimit: 60
|         ThrottlingRateLimit: 30
|     Auth:
|       RequestValidators:
|         contact-body:
|           ValidateRequestBody: true
|       Models:
|         ContactRequest: <JSON Schema>
|         TrackingRequest: <JSON Schema>
|     AccessLogSetting:
|       DestinationArn: !GetAtt AccessLogGroup.Arn
|       Format: <JSON format with $context.identity.sourceIp, ...>
|
+-- AWS::DynamoDB::Table                RateLimitRulesTable
|     TableName: rate_limit_rules
|     BillingMode: PAY_PER_REQUEST
|     AttributeDefinitions: [rule_key: S]
|     KeySchema: [rule_key: HASH]
|     TimeToLiveSpecification:                 # Para blacklist auto con TTL
|       AttributeName: expires_at
|       Enabled: true
|     SSESpecification: { SSEEnabled: true }
|     # Items: "endpoint#/contact" + "endpoint#/track" + "ip#X.X.X.X" (white/blacklist)
|     #        + "country#CN" (country rules)
|     # Volumen ~10-50 items. Cacheable via common/cache @cached(ttl=60)
|
+-- AWS::DynamoDB::Table                RateLimitBucketsTable
|     TableName: rate_limit_buckets
|     BillingMode: PAY_PER_REQUEST
|     AttributeDefinitions: [bucket_key: S]
|     KeySchema: [bucket_key: HASH]
|     TimeToLiveSpecification:                 # Auto-cleanup de ventanas pasadas
|       AttributeName: expires_at
|       Enabled: true
|     # Items: "<ip>#<endpoint>#<window_start_epoch>"
|     # Atomic INCREMENT counter via UpdateItem ADD
|     # TTL = window_start + window_seconds + 60s grace
|     # Volumen ~30k items vivos rotando. Free tier perpetuo lo cubre
|
+-- AWS::DynamoDB::Table                ContactsTable
|     BillingMode: PAY_PER_REQUEST
|     PointInTimeRecoverySpecification: { Enabled: true }
|     AttributeDefinitions: [id: S]
|     KeySchema: [id: HASH]
|     StreamSpecification:                 # Para stream_processor -> Neon
|       StreamViewType: NEW_AND_OLD_IMAGES
|
+-- AWS::DynamoDB::Table                TrackingTable
|     BillingMode: PAY_PER_REQUEST
|     AttributeDefinitions: [session_id: S, page_id: S]
|     KeySchema: [session_id: HASH, page_id: RANGE]
|     TimeToLiveSpecification:
|       AttributeName: expires_at
|       Enabled: true
|     StreamSpecification:                 # Para stream_processor -> Neon
|       StreamViewType: NEW_AND_OLD_IMAGES
|
+-- AWS::DynamoDB::Table                CacheTable
|     BillingMode: PAY_PER_REQUEST
|     AttributeDefinitions: [cache_key: S]
|     KeySchema: [cache_key: HASH]
|     TimeToLiveSpecification:
|       AttributeName: expires_at         # Auto-delete cuando TTL expira
|       Enabled: true
|     SSESpecification:
|       SSEEnabled: true                  # Encrypted at rest (AWS-owned key)
|     # Tabla generica de cache (src/common/cache/)
|     # Free tier: 25GB + 25 WCU + 25 RCU perpetuo lo cubre
|     # Sin Streams (cache no es source of truth)
|
+-- AWS::SES::ConfigurationSet          PortfolioSesConfig
|     DeliveryOptions: { TlsPolicy: REQUIRE }
|     ReputationOptions: { ReputationMetricsEnabled: true }
|
+-- AWS::SES::ConfigurationSetEventDestination
|     ConfigurationSetName: !Ref PortfolioSesConfig
|     EventDestination:
|       MatchingEventTypes: [BOUNCE, COMPLAINT, DELIVERY]
|       SnsDestination: !Ref BounceComplaintTopic
|
+-- AWS::SNS::Topic                     BounceComplaintTopic
|     (Subscribe owner email)
|
+-- AWS::Logs::LogGroup                 AccessLogGroup
|     RetentionInDays: 30
|
+-- AWS::Logs::LogGroup                 ContactFormLogGroup
|     LogGroupName: /aws/lambda/contact-form
|     RetentionInDays: 30
|
+-- AWS::Logs::LogGroup                 TrackingPixelLogGroup
|     RetentionInDays: 14
|
+-- AWS::CloudWatch::Alarm              ThrottleAnomalyAlarm
|     MetricName: ThrottledRequests
|     Threshold: 10
|     Period: 300
|     AlarmActions: [!Ref AlertsTopic]
|
+-- AWS::CloudWatch::Alarm              ContactErrorAlarm
|     MetricName: 5XXError
|     Threshold: 1
|     Period: 300
|
+-- AWS::SNS::Topic                     AlertsTopic
      (Subscribe owner email)

NOT in template.yaml (manual via CLI o consola, una vez):
  - SSM Parameter: /portfolio/turnstile-secret (SecureString + KMS)
  - SSM Parameter: /portfolio/neon-url (SecureString + KMS, connection string)
  - SSM Parameter: /portfolio/owner-email (String)
  - SSM Parameter: /portfolio/ses-from-address (String)
  - SES Domain Identity: the-full-stack.com (DKIM CNAMEs en Cloudflare)
  - ACM Certificate para api.the-full-stack.com (us-west-2)
  - API Gateway Custom Domain + BasePathMapping
  - Neon project + database + branches (via neonctl o dashboard)
  - Neon DB schema (via `serverless db-migrate` despues del deploy)
  - Cloudflare DNS: 3 CNAMEs DKIM + 1 TXT SPF + 1 TXT DMARC
  - Cloudflare Turnstile widget creado en dashboard
    + 6 hostnames registrados (the-full-stack.com + 5 subdominios)
```

---

## 8. Diagrama del flujo de deploy

```
Developer local
       |
       | 1. clone + uv sync
       v
+----------------------+
| serverless/          |
| (en root del repo)   |
+----------------------+
       |
       | 2. Editar handler / template
       v
+----------------------+
| sam validate         |    Sanity check sintactico
+----------------------+
       |
       | 3. Tests locales
       v
+----------------------+
| pytest tests/unit    |    Coverage >= 80% per-file
+----------------------+
       |
       | 4. sam local invoke (event JSON)
       v
+----------------------+
| Lambda runs in Docker|    Sin AWS, con moto mocks
+----------------------+
       |
       | 5. sam local start-api (integracion)
       v
+----------------------+
| curl POST localhost  |
+----------------------+
       |
       | 6. sam build --use-container
       v
+----------------------+
| .aws-sam/build/      |    Build cross-platform Linux
+----------------------+
       |
       | 7. sam deploy --guided (1ra vez)
       |    sam deploy           (subsiguientes)
       v
+----------------------+
| CloudFormation       |    AWS crea / actualiza recursos
| stack: portfolio-    |    idempotente
| backend              |
+----------------------+
       |
       | 8. Outputs: API URL + CloudFront alias
       v
+----------------------+
| Smoke test           |    scripts/smoke_test.sh
| curl contra prod URL |
+----------------------+
       |
       | 9. Verificar logs primeras invocaciones
       v
+----------------------+
| sam logs --tail      |    CloudWatch real-time
+----------------------+
       |
       | 10. Configurar Turnstile widget
       |     + 6 hostnames en dashboard CF
       v
+----------------------+
| Test E2E browser     |    Form real desde *.the-full-stack.com
+----------------------+
```

---

## 9. Convenciones aplicadas

| Convencion | Origen | Aplicacion en `serverless/` |
|------------|--------|-----------------------------|
| Carpetas por dominio (services, selectors, handlers) | `.claude/rules/python.md` + `.claude/rules/django.md` | `src/<lambda>/` con `handler.py` + `service.py` + `persistence.py` + `schemas.py` |
| Un archivo por entidad < 300 lineas | `.claude/rules/python.md` | Cada Lambda esta dividida en handler/service/persistence/schemas |
| Type hints obligatorios | `.claude/rules/python.md` | `src/common/types.py` con TypedDicts compartidos |
| Single quotes para strings tecnicos | `.claude/rules/python.md` | Codigo Python en todo el modulo |
| Trailing commas | `.claude/rules/python.md` | Minimiza git diff en multilinea |
| pytest path-mirroring | `.claude/rules/python.md` + `.claude/rules/django.md` | `tests/unit/<X>/test_<Y>.py` mirror de `src/<X>/<Y>.py` |
| BDD-style en docstring | `.claude/rules/python.md` | Tests con Given/When/Then en docstring + AAA en cuerpo |
| Asserts EXACTOS | `.claude/rules/python.md` | `assert response == {...}`, no rangos |
| ADR para cada decision estructural | nuevo en este proyecto | `docs/adr/<N>-*.md` numerado, formato corto |
| Knowledge tree READMEs | `.claude/rules/markdown-docs.md` | `README.md` + `ARCHITECTURE.md` + `DEPLOYMENT.md` + `RUNBOOK.md` |
| Sin atribucion IA | `~/.claude/CLAUDE.md` + repo policy | Todos los archivos limpios |
| Sin emojis | `.claude/rules/markdown-docs.md` | Solo ASCII en este doc |
| IAM least privilege | `.claude/docs/aws-lambda/06-iam-security.md` | Cada Lambda tiene solo los permisos minimos en template.yaml |
| Secrets en SSM + KMS | `.claude/docs/aws-lambda/06-iam-security.md` | Turnstile secret NUNCA en env vars planos |
| Defense in depth | `.claude/docs/serverless-rate-limit/01-why-not-waf.md` | 5 capas (Cloudflare upstream + middleware DynamoDB + reserved concurrency + API GW + validator + alarms) |

---

## 10. Que NO esta en `serverless/` (intencional)

- **Frontend (ContactForm.astro, TrackingPixel.astro, CookieBanner.astro)**: viven en `packages/ui/src/components/` porque son componentes Astro compartidos en las 6 apps. Solo el backend en `serverless/`.
- **Migrations DynamoDB**: no aplican (NoSQL schema-less por diseno, la "migration" es modificar el template y `sam deploy`).
- **GitHub Actions workflow para deploy**: futuro, va en `.github/workflows/deploy-backend.yml`. Por ahora deploy es manual local (segun el patron actual de cloudflare-deploy).
- **MJML compiler bundled**: el `.html` queda committed al repo. Recompilar es opt-in via `scripts/compile_mjml.mjs`. Evita dep de Node en runtime Lambda.
- **Server Django stub**: ya existe en `server/` para futuro Django, no se mezcla con `serverless/` (AWS Lambdas).
