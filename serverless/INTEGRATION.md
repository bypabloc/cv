# Propuesta de integracion: DynamoDB + Neon PostgreSQL + Cache

> Documento de diseno que conecta las 4 piezas del backend del
> portfolio:
>
> 1. **DynamoDB** (hot path, writes desde Lambdas)
> 2. **DynamoDB Streams + stream_processor Lambda** (replica near-real-time a PG)
> 3. **Neon PostgreSQL 18** (analytics + CRM-style queries + dashboards)
> 4. **Cache module en common/** (TTL-based key-value, generic, reusable por todas las Lambdas)
>
> Decision base: investigacion en `.claude/docs/{aws-lambda,aws-dynamodb,aws-ses,aws-api-gateway,cloudflare-turnstile,postgresql-18-analytics,neon,dynamodb-cache}/`.

---

## 1. Por que esta arquitectura

### Restricciones del proyecto

- **Volumen bajo-medio**: 200 contacts/mes + 15.000 tracking events/mes
- **Latencia hot path importa**: form submit no debe pasar de 800ms total (Turnstile siteverify domina)
- **Costo objetivo**: ~$7/mes (WAF Web ACL fijo); el resto debe caber en free tier perpetuo
- **Solo developer**: zero-ops, no managed instances, no VPC, no fine-tuning de capacity
- **Analytics CRM-style requeridos**: contacts por mes/niche, conversion rate, top landing pages, session journey, daily metrics

### Por que NO una sola DB

| Stack candidato | Pros | Contras | Verdict |
|-----------------|------|---------|---------|
| Solo DynamoDB | Free tier perpetuo, low-latency writes, scale automatic | NoSQL no soporta window functions / joins / agregaciones complejas. Para analytics requeririamos hacer scan completo + procesamiento en Lambda (costoso, lento) | Insuficiente para analytics |
| Solo Neon PG | SQL nativo, window functions, JSONB, full-text search, branching | Cold start de psycopg3 (~150-250ms) en cada Lambda del hot path. Sin scale-to-zero al 100% (scale-down a 0.25 CU). Connection pool fragil con concurrent Lambdas | Compromete latencia hot path |
| Solo Redis (ElastiCache) | Sub-ms latency | $14+/mes minimo, VPC obligatorio (+10s cold start Lambda), no persistencia para analytics | Caro + complejo + insuficiente |
| Solo Momento | Scale-to-zero, simple API HTTP | Vendor lock-in, no SQL para analytics | Insuficiente para analytics |

### Por que hibrido

**DynamoDB como source of truth del hot path**:

- Writes a Dynamo son <10ms p99 (warm) — el form responde rapido
- Free tier perpetuo (25 WCU + 25 RCU + 25 GB) cubre todo el volumen
- TTL nativo sin costo para tracking 60d retention
- IAM scope estricto por tabla, sin VPC, sin connection pool

**Neon como read replica analitica**:

- SQL standard para queries que serian agonia en NoSQL
- Free tier 0.5GB + 191.9h compute/mes (cabe; el portfolio es idle 95% del tiempo)
- Scale-to-zero auto despues de 5 min sin queries -> $0 idle
- Branching git-style para preview environments
- PG18: virtual generated columns, skip scan, AIO, UUIDv7 nativo

**Streams como pegamento**:

- DynamoDB Streams emite eventos por cada write (NEW_AND_OLD_IMAGES)
- Lag tipico 5-30s entre write Dynamo y read en PG -> aceptable para analytics
- Free tier: primeros 2.5M GetRecords/mes gratis
- Sin polling externo, sin cron de import

**Cache para reducir reads repetitivos**:

- Lambdas warm reusan client boto3, pero SSM `get_parameter` aun cuesta ~30ms y $0.05/10K calls
- Caching de Turnstile secret, country lookups, queries agregadas Neon
- TTL nativo Dynamo + lock distribuido + SWR + tag invalidation

---

## 2. Modelo de datos: que vive donde

| Workload | DynamoDB | Neon PG | Cache |
|----------|----------|---------|-------|
| Form submission save (hot path) | source of truth | replica via Stream | NO |
| Tracking pixel save (hot path) | source of truth (TTL 60d) | replica via Stream | NO |
| TTL auto-delete tracking | YES (60d) | drop partition mensual | NO |
| Turnstile secret SSM lookup | NO | NO | YES (300s) |
| Neon URL SSM lookup | NO | NO | YES (300s) |
| Country lookup (IP -> country) | NO | NO | YES (24h) |
| User-Agent parsing | NO | NO | YES (24h) |
| Daily metrics query | NO | YES (computed nightly) | YES (30min SWR) |
| Top landing pages | NO | YES (materialized view) | YES (30min SWR) |
| Session journey (LAG/LEAD) | NO | YES (mv refresh nightly) | NO |
| Contacts CRM filtering | NO | YES (CITEXT + GIN) | NO |
| Full-text search en messages | NO | YES (to_tsvector spanish + GIN) | NO |
| Joins entre contacts + tracking | NO | YES | NO |
| Conversion rate dashboard | NO | YES (daily_metrics tabla) | YES (30min SWR) |

Regla mnemotecnica:

- **Lambda escribe** -> DynamoDB
- **Owner consulta para CRM/analytics** -> Neon
- **Lambda lee valores caros que se repiten** -> Cache

---

## 3. Flujo de datos end-to-end

### 3.1. Form de contacto

```text
Browser  POST /contact + Turnstile token
    |
    v
WAF rate-limit 3 req/5min/IP
    |
    v
API Gateway REST + JSON validator
    |
    v
Lambda contact_form
    |
    +--(1)--> Cache.get('ssm:turnstile-secret') -> HIT (warm)
    |                                            -> MISS first time -> ssm.get_parameter
    |
    +--(2)--> Turnstile siteverify (httpx) -> success=true, hostname OK
    |
    +--(3)--> DynamoDB PUT contacts (id=UUIDv7)   < 10ms p99
    |
    +--(4)--> SES SendEmail al owner               ~ 200ms
    |
    v
Response 200 OK { contact_id }
    |
    | === ASINC: DynamoDB Stream emite el INSERT ===
    v
DynamoDB Stream record (eventID, NewImage)
    |
    | batch=100, window=10s
    v
Lambda stream_processor
    |
    +--(a)--> Idempotency check: SELECT 1 FROM processed_stream_events WHERE event_id=?
    |
    +--(b)--> Cache.get('ssm:neon-url') -> HIT (warm)
    |
    +--(c)--> psycopg3 cached conn -> UPSERT INTO contacts (...) ON CONFLICT (stream_event_id) DO NOTHING
    |
    +--(d)--> INSERT processed_stream_events (event_id, ...)
    |
    v
PG contacts table updated (lag total ~10-30s)
    |
    | === ASINC nightly 03:00 UTC ===
    v
Lambda aggregator
    |
    +--(i)--> SELECT count, group by date+niche FROM contacts
    +--(ii)-> UPSERT daily_metrics
    +--(iii)-> REFRESH MATERIALIZED VIEW mv_contacts_by_month_niche
    +--(iv)-> Cache.invalidate(tag='analytics')
```

### 3.2. Tracking pixel (consent dado)

```text
Browser onLoad (consent cookie YES)
    |
    | + invisible Turnstile token (best-effort)
    v
POST /track con signals (UA, viewport, UTMs, etc.)
    |
    v
WAF rate-limit 30 req/5min/IP
    |
    v
API Gateway REST
    |
    v
Lambda tracking_pixel
    |
    +--(1)--> Cache.get('geo:'+ip) -> HIT (90% de los casos)
    |                              -> MISS -> CF-IPCountry header
    |
    +--(2)--> Cache.get('ua-parse:'+ua_hash) -> HIT (warm)
    |                                        -> MISS -> parse UA
    |
    +--(3)--> DynamoDB PUT tracking (session_id, page_id=UUIDv7, expires_at = now + 60d)
    |
    v
Response 204 No Content
    |
    | === ASINC: Stream INSERT ===
    v
Lambda stream_processor
    |
    +--(a)--> UPSERT tracking_events (particion del mes correcto)
    |
    v
PG tracking_events table updated
    |
    | === ASINC: Stream REMOVE (TTL fired despues de 60d) ===
    v
Lambda stream_processor
    |
    +--(no-op para PG: la particion mensual se drop por aggregator)
    |
    v
DynamoDB row eliminado por TTL service de AWS
```

### 3.3. Cache lookup tipico

```text
Lambda  (warm execution)
    |
    | @cached(ttl=300, stale_for=600, namespace='ssm', tags=['secrets'])
    | def get_turnstile_secret() -> str: ...
    v
DynamoDBCache.get('ssm:get_turnstile_secret:<hash>')
    |
    +-- GetItem en tabla `cache` (PK=cache_key)
    |
    +--+ fresh    -> return cached value (HIT, ~5ms)
       |
       +-- stale   -> return cached value
       |              + asyncio.create_task(_refresh_async)
       |
       +-- expired -> acquire_lock (ConditionalWrite)
       |              -> if OK: recompute (ssm.get_parameter), set, release lock
       |              -> if NO: busy-wait 500ms, return stale or recompute
       |
       +-- miss    -> mismo path que expired
```

---

## 4. Idempotency strategy

Tres niveles:

| Nivel | Donde | Mecanismo | Caso de uso |
|-------|-------|-----------|-------------|
| API Gateway | Request layer | (sin idempotency nativo en API GW REST) | N/A |
| Lambda handler | Powertools `@idempotent` | Hash del event body + DynamoDB idempotency-store (separada del cache) | Form submit (evita duplicate email si CF retries) |
| Stream consumer | stream_processor | Idempotency log table en Neon: `processed_stream_events` PK=event_id | Re-procesar misma record del Stream sin duplicar |
| Cache | common/cache | NA - idempotency NO se usa para cache, son cosas distintas | Solo memoization |

Ver `.claude/docs/dynamodb-cache/07-powertools-idempotency-vs-cache.md` para la
distincion entre `@idempotent` (no re-ejecutar handler) y `@cached` (no
recomputar valor).

---

## 5. Costos consolidados (us-west-2, Mayo 2026)

| Componente | Cost/mes |
|------------|----------|
| AWS WAF Web ACL (fijo) | $5.00 |
| AWS WAF rate-based rules (2) | $1.20 |
| AWS WAF requests | ~$0.01 |
| API Gateway REST (~30k req/mo) | $0.10 |
| Lambda invocations (5 funciones, ~50k total) | $0 (free tier 1M/mo) |
| Lambda compute GB-sec | $0 (free tier 400k GB-sec/mo) |
| DynamoDB writes (~25k/mo total 3 tablas) | $0 (free tier 1M/mo) |
| DynamoDB reads (cache + Lambdas, ~200k/mo) | $0 (free tier 2.5M/mo) |
| DynamoDB storage | $0 (free tier 25 GB) |
| DynamoDB Streams (~30k records/mo) | $0 (free tier 2.5M GetRecords) |
| SES emails (~200/mo) | $0 (free tier 62k Lambda outbound) |
| CloudWatch Logs (10 GB/mo) | ~$0.50 |
| CloudWatch Alarms (~10) | $1.00 |
| X-Ray traces sampled | <$0.01 |
| SQS DLQ (StreamProcessor) | $0 |
| SNS notifications | $0 |
| Neon free tier (0.5GB + 191.9h compute) | $0 |
| Cloudflare Turnstile (unlimited free) | $0 |
| **TOTAL estimado** | **~$7.81/mes** |

Si el portfolio escala 10x (~300k req/mo):

- WAF sigue $7.21 (fijo + rules)
- Lambda $0 (aun en free tier)
- DynamoDB $0 (aun en free tier)
- Neon $0 (Free) o $19 si pasa a Launch plan
- **Total escala-10x**: ~$8/mes o $27/mes con Neon Launch

---

## 6. Roadmap de implementacion

| Fase | Deliverable | Estimacion |
|------|-------------|------------|
| Fase 1 | SAM template + 3 Lambdas hot path (contact_form, tracking_pixel, turnstile_validator) + WAF + API GW + 2 tablas Dynamo + SES | 1-2 dias |
| Fase 2 | Cache module en `src/common/cache/` + tabla `cache` + tests + integracion en 3 Lambdas existentes | 1 dia |
| Fase 3 | Neon project setup + migrations 001-005 + connection via psycopg3 layer | 1 dia |
| Fase 4 | stream_processor Lambda + Streams enabled en Dynamo tables + DLQ + idempotency log | 1-2 dias |
| Fase 5 | aggregator Lambda + EventBridge cron + materialized views + daily_metrics | 1-2 dias |
| Fase 6 | Frontend integration (ContactForm.astro + TrackingPixel.astro + CookieBanner.astro en packages/ui) | 1-2 dias |
| Fase 7 | Dashboard (Astro page protegida con basic auth o magic link) que consulta Neon | 2-3 dias |
| Fase 8 | Observability dashboard + alarms + smoke tests + runbook | 1 dia |

**Total estimado**: 9-15 dias de trabajo (no full-time).

Cada fase es deployable independientemente. La fase 1 + 6 ya es un MVP
funcional (sin analytics, solo form de contacto). Las fases 2-5 son
incrementales y no rompen la 1.

---

## 7. Anti-patterns evitados explicitamente

- **Dual write Lambda -> Dynamo + PG**: introduciria 2 source of truth + complejidad de consistencia. La fuente unica es Dynamo; PG es replica.
- **Lambda direct a Neon en hot path**: psycopg3 cold start (~250ms) + conn pool fragil. Evitado al mover write a Dynamo + replica async.
- **PG sin TTL para tracking**: PG no tiene TTL nativo; `DELETE WHERE expires_at < now()` es expensive. Solucion: range partitioning + drop partition mensual via pg_partman.
- **Cache sin lock distribuido**: thundering herd cuando expira un secret muy usado. Solucion: lock + XFetch + SWR.
- **Cache compartiendo tabla con datos hot**: contaminaria DynamoDB Streams (eventos cache no son interesantes). Solucion: tabla `cache` dedicada sin Streams.
- **Single-table design forzado**: `contacts`, `tracking`, `cache` son dominios distintos. 3 tablas separadas evitan PK schema complejo + GSI proliferation.
- **GitHub Actions deploy del backend en CI**: por ahora deploy manual local (mismo patron que cloudflare-deploy). CI workflow es Fase 8+.
- **VPC para Neon**: Neon es publico con SSL + IP allowlist. VPC anadiria 10s cold start. Evitado.
- **Connection pool en Lambda con N=20**: cold start crece linealmente. Solucion: 1 conn cached en module scope; reserved concurrency=2 en stream_processor limita conexiones concurrentes a Neon.

---

## 8. Skills relacionadas (invocables por nombre)

Para preguntas sobre cada pieza, la skill correspondiente tiene la
respuesta consolidada del proyecto:

- `/aws-lambda-python` — handlers, Powertools, IAM
- `/aws-api-gateway` — REST API, throttling, WAF
- `/aws-dynamodb` — tablas, On-Demand, TTL, boto3
- `/aws-ses` — DKIM/SPF/DMARC, transactional email
- `/cloudflare-turnstile` — captcha widget + siteverify
- `/neon` — serverless PG, branching, psycopg3 in Lambda
- `/dynamodb-cache` — cache patterns, lock, SWR, invalidation
- `/postgresql-18` — features generales PG18 (skill existente)
- `.claude/docs/postgresql-18-analytics/` — schema + queries de este proyecto (sin skill, solo docs)

---

## 9. Navegacion

- [README.md](README.md) — Indice del modulo
- [ARCHITECTURE.md](ARCHITECTURE.md) — Estructura completa + diagramas ASCII
- [DEPLOYMENT.md](DEPLOYMENT.md) — Pasos primer deploy (a crear)
- [RUNBOOK.md](RUNBOOK.md) — Operaciones post-deploy (a crear)
- [devtools/serverless/README.md](../devtools/serverless/README.md) — CLI del modulo
- [.claude/docs/](../.claude/docs/) — Knowledge base de cada servicio
