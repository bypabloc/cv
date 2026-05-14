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
- **Costo objetivo**: $0/mes (sin WAF, sin CloudWatch Alarms, retention logs 7d, todo en free tier perpetuo)
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

| Workload | DynamoDB | Neon PG | Cache | Rate-limit |
|----------|----------|---------|-------|------------|
| Form submission save (hot path) | source of truth | replica via Stream | NO | check antes |
| Tracking pixel save (hot path) | source of truth (TTL 60d) | replica via Stream | NO | check antes |
| TTL auto-delete tracking | YES (60d) | drop partition mensual | NO | NO |
| Turnstile secret SSM lookup | NO | NO | YES (300s) | NO |
| Neon URL SSM lookup | NO | NO | YES (300s) | NO |
| Country lookup (IP -> country) | NO | NO | YES (24h) | NO |
| User-Agent parsing | NO | NO | YES (24h) | NO |
| Rate-limit rules (endpoint, IP, country) | dedicated table | NO | cached 60s | source |
| Rate-limit counters (per IP+window) | dedicated table | NO | NEVER cache | source |
| Auto-blacklist (3+ tokens en 60s) | rule kind=ip_blacklist TTL 24h | NO | NO | write |
| Daily metrics query | NO | YES (computed nightly) | YES (30min SWR) | NO |
| Top landing pages | NO | YES (materialized view) | YES (30min SWR) | NO |
| Session journey (LAG/LEAD) | NO | YES (mv refresh nightly) | NO | NO |
| Contacts CRM filtering | NO | YES (CITEXT + GIN) | NO | NO |
| Full-text search en messages | NO | YES (to_tsvector spanish + GIN) | NO | NO |
| Joins entre contacts + tracking | NO | YES | NO | NO |
| Conversion rate dashboard | NO | YES (daily_metrics tabla) | YES (30min SWR) | NO |

Regla mnemotecnica:

- **Lambda escribe** -> DynamoDB
- **Owner consulta para CRM/analytics** -> Neon
- **Lambda lee valores caros que se repiten** -> Cache
- **Lambda valida limite per-IP** -> Rate-limit module

---

## 3. Flujo de datos end-to-end

### 3.1. Form de contacto

```text
Browser  POST /contact + Turnstile token
    |
    v
Cloudflare DDoS + Bot Fight (free upstream)
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
Cloudflare DDoS + Bot Fight (free upstream)
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

## 5. Costos consolidados (us-east-1, Mayo 2026)

Arquitectura SIN AWS WAF, SIN CloudWatch Alarms, retention logs 7 dias.
Objetivo: $0/mes operacional.

| Componente | Cost/mes |
|------------|----------|
| API Gateway REST (~30k req/mo) | $0 (free tier 1M req/mo primer ano; despues $0.10) |
| Lambda invocations (5 funciones, ~50k total) | $0 (free tier 1M/mo PERPETUO) |
| Lambda compute GB-sec | $0 (free tier 400k GB-sec/mo PERPETUO) |
| DynamoDB writes (~60k/mo, 5 tablas) | $0 (free tier 1M/mo PERPETUO) |
| DynamoDB reads (~250k/mo) | $0 (free tier 2.5M/mo PERPETUO) |
| DynamoDB storage (~5GB total) | $0 (free tier 25GB PERPETUO) |
| DynamoDB Streams (~30k records/mo) | $0 (free tier 2.5M GetRecords PERPETUO) |
| SES emails (~200/mo, desde Lambda) | $0 (free tier 62k/mo PERPETUO) |
| CloudWatch Logs ingest (~1-2GB/mo con retention 7d + INFO level) | $0 (free tier 5GB ingest/mo PERPETUO) |
| CloudWatch Logs storage | $0 (retention 7d mantiene <0.5GB; free tier 5GB) |
| CloudWatch metrics custom Powertools | $0 (free tier 10 metrics PERPETUO) |
| CloudWatch Alarms | $0 (NINGUNA configurada; solo AWS Billing Alarm global, gratis) |
| X-Ray traces sampled | $0 (free tier 100k traces/mo PERPETUO) |
| SQS DLQ (StreamProcessor) | $0 (free tier 1M req/mo PERPETUO) |
| SNS notifications | $0 (free tier 1M publishes/mo PERPETUO) |
| Neon free tier (0.5GB + 191.9h compute) | $0 |
| Cloudflare Turnstile (unlimited free) | $0 |
| Cloudflare Pages + DDoS (upstream del browser) | $0 |
| **TOTAL operacional** | **$0/mes** |

A escala 10x (~300k req/mo):

- Lambda $0 (aun free tier 1M invocations/mes)
- DynamoDB $0 (aun free tier; rate_limit_buckets crece a ~300k pero TTL lo limpia)
- CloudWatch Logs $0 (1-2GB con retention 7d sigue dentro de 5GB free)
- API Gateway: $0.30 si pasaste el primer ano (despues del free tier inicial)
- Neon $0 (Free tier) o $19 si pasa a Launch plan
- **Total escala-10x**: $0.30/mes o $19.30/mes con Neon Launch

### Ahorro vs arquitectura inicial con AWS WAF + Alarmas

| Configuracion | Cost/mes | Ahorro |
|---------------|----------|--------|
| Con WAF Web ACL + 12 Alarms + Logs 30d | ~$7.81 | - |
| Sin WAF (rate-limit DynamoDB) + 12 Alarms + Logs 30d | ~$1.71 | $6.10 |
| Sin WAF + sin Alarms + Logs 7d (ESTE) | **$0** | **$7.81/mes** ($94/ano) |

### Decisiones de costo-cero

1. **NO AWS WAF**: rate-limit en middleware Lambda + DynamoDB ($0 vs $7/mes)
2. **NO CloudWatch Alarms operacionales**: solo AWS Billing Alarm global gratis ($0 vs $1.20/mes)
3. **CloudWatch Logs retention 7d + INFO level**: cabe en 5GB free tier vs $0.50/mes con retention 30d + DEBUG
4. **Lambda arm64 Graviton2**: -20% costo + +19% performance (relevante cuando se sale del free tier)
5. **DynamoDB On-Demand**: free tier perpetuo lo cubre; Provisioned daria $12/mes minimo
6. **Reserved concurrency baja**: contiene gastos en caso de ataque sostenido (5 contact_form / 20 tracking)
7. **Sin VPC, sin NAT Gateway**: NAT Gateway cuesta $32/mes + GB transferido. Evitado.
8. **Sin ACM cert para API custom domain en MVP**: usar API Gateway default URL (postpone custom domain a fase 7)

### Trade-offs vs WAF

| Aspecto | Con WAF | Sin WAF (este) |
|---------|---------|----------------|
| Costo | $7/mes | $0 (free tier) |
| Defense edge (rechaza antes de Lambda) | YES | NO (siempre invoca) |
| Per-IP rate-limit | nativo | middleware en Lambda |
| Algoritmo | fixed window | sliding window weighted (mejor smoothing) |
| Whitelist/blacklist IP custom | manual via WAF | en `rate_limit_rules` table |
| Auto-blacklist bot detection | NO | YES (3+ tokens validos en 60s) |
| Country rules dinamicas | WAF GeoMatch | en `rate_limit_rules` table |
| OWASP managed rules | YES (gratis bundle) | NO (mitigado por Turnstile + JSON Schema) |
| Scale bajo DDoS sostenido | infinito | depende de Cloudflare upstream + reserved concurrency |
| Latencia agregada al hot path | <5ms | ~10-20ms warm (2 GetItem + 1 UpdateItem) |
| Logs/dashboards | nativos en consola | CloudWatch Logs + queries custom |

**Cuando migrar de vuelta a WAF**: si el portfolio recibe ataques DDoS
sostenidos >10k req/s por horas y CloudWatch billing dispara alarma de
Lambda invocations. El primer indicador sera la metrica `AutoBlacklistTriggered`
> 100/hora.

---

## 6. Roadmap de implementacion

| Fase | Deliverable | Estimacion |
|------|-------------|------------|
| Fase 1 | SAM template + 3 Lambdas hot path (contact_form, tracking_pixel, turnstile_validator) + API GW + 2 tablas Dynamo + SES (sin WAF) | 1-2 dias |
| Fase 1.5 | Modulo `common/rate_limit/` + 2 tablas rate_limit + reglas iniciales + integracion en contact_form/tracking_pixel | 1 dia |
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
- `/aws-api-gateway` — REST API, throttling global (sin per-IP en este diseno)
- `/serverless-rate-limit` — Rate-limit per-IP self-managed con DynamoDB (alternativa $0 a WAF)
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
