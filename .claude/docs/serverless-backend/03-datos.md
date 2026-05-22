# 03 — Datos: DynamoDB y Neon

> [<- 02-flujos](02-flujos.md) | [Siguiente: 04-deploy-operacion ->](04-deploy-operacion.md)

El backend usa storage hibrido: DynamoDB es el source of truth del hot
path (writes desde los Lambdas), Neon PostgreSQL es la replica analitica
(queries CRM-style, joins, window functions).

## 1. Que dato vive donde

| Workload | DynamoDB | Neon PG |
|----------|----------|---------|
| Form submission save (hot path) | source of truth | replica via Stream |
| Tracking event save (hot path) | source of truth (TTL 60d) | replica via Stream |
| Auto-delete tracking a los 60d | TTL nativo (0 WCU) | drop de particion mensual |
| Owner consulta CRM / analytics | NO | SI (joins, window funcs, full-text) |
| Cache de valores caros (SSM, parsing) | tabla `cache` | NO |
| Rate-limit (rules + counters) | tablas `rate-limit-*` | NO |

Regla mnemotecnica: **Lambda escribe -> DynamoDB**; **owner consulta ->
Neon**; **Lambda lee valores caros repetidos -> cache (DynamoDB)**;
**Lambda valida limite per-IP -> rate-limit (DynamoDB)**.

El pegamento entre ambos es DynamoDB Streams + el Lambda
`stream_processor` (ver [02-flujos.md](02-flujos.md)). Lag tipico de
replica: 5-30s.

## 2. Las 5 tablas DynamoDB

Cada tabla es su propio stack de recurso
(`portfolio-dynamodb-<tabla>-<stage>`), modo `PAY_PER_REQUEST`. Nombre
real de la tabla: `portfolio-<tabla>-<stage>`. Cada stack publica el
nombre y el ARN a SSM (`/portfolio/{stage}/dynamodb/<tabla>/{name,arn}`).

### `contacts` — form de contacto

```text
PK (HASH): id  (S, UUIDv7)
Stream: NEW_AND_OLD_IMAGES   PITR: enabled   sin TTL (se retienen todos)

email  name  message
service_type   enum: freelance|contract|part-time|tech-lead|consulting|other
company  role  budget  timeline   (opcionales)
source_url           pagina exacta del envio
source_subdomain     cual de los 6 niches
ip_address           CF-Connecting-IP
country              CF-IPCountry (2 chars)
user_agent
turnstile_hostname   para auditoria
created_at           ISO8601
```

### `tracking` — eventos de tracking

```text
PK (HASH): session_id  (S)
SK (RANGE): page_id     (S, UUIDv7 -> sort por tiempo natural)
Stream: NEW_AND_OLD_IMAGES   PITR: disabled (data efimera)
TTL: expires_at

url  path  referrer
utm_source utm_medium utm_campaign utm_term utm_content   (opcionales)
screen_res  viewport
device_type   desktop|mobile|tablet
browser  os  lang  timezone
ip_address  country  user_agent  source_subdomain
created_at    ISO8601
expires_at    (N, Unix epoch) -> AWS auto-borra +60d, 0 WCU
```

### `cache` — cache de proposito general

```text
PK (HASH): cache_key  (S)   ej. "ssm:get_turnstile_secret:<hash>"
TTL: expires_at      SSE: enabled      sin Stream

value         JSON serializado
value_type    string|json|bytes_b64
created_at    ISO8601
expires_at    (N, epoch) -> TTL attribute
stale_until   (N, epoch) -> fin de la ventana stale-while-revalidate
tags          (SS) -> invalidacion bulk por tag
lock_owner    (S) -> request_id del Lambda que tiene el lock
lock_expires  (N) -> TTL del lock distribuido
```

Lo usan `contact_form` y `tracking_pixel` via `shared/cache/`. Detalle
de patrones (lock distribuido, SWR, invalidacion): skill `dynamodb-cache`.

### `rate-limit-rules` — reglas de rate-limit

```text
PK (HASH): rule_key  (S)
   patrones: "endpoint#/contact"  "endpoint#/track"  "endpoint#*"
             "ip#X.X.X.X"  (white o blacklist)   "country#XX"
TTL: expires_at  (auto-expira las entradas de auto-blacklist)

kind             endpoint|ip_whitelist|ip_blacklist|country
limit            (N) max requests en la ventana
window_seconds   (N) tamano de la ventana
action           allow|block|throttle
expires_at       (N) TTL para blacklist auto (+24h)
reason           texto descriptivo (auditoria)
created_at  created_by   manual|cli|auto-detected
```

### `rate-limit-buckets` — contadores per-IP

```text
PK (HASH): bucket_key  (S)
   patron: "<ip>#<endpoint>#<window_start_epoch>"
TTL: expires_at  (limpia ventanas pasadas)

count             (N) contador atomico (UpdateItem ADD)
window_start      (N, epoch)   window_seconds  (N)
first_request  last_request    (ISO8601)
turnstile_tokens  (N) contador de tokens validos (bot detection)
expires_at        (N) window_start + window_seconds + 60s de gracia
```

`rate-limit-rules` y `rate-limit-buckets` las usan `contact_form` y
`tracking_pixel` via `shared/rate_limit/`. Algoritmo (sliding window
weighted, auto-blacklist): skill `serverless-rate-limit`.

## 3. Tablas Neon PostgreSQL

Neon es la replica analitica. El schema lo definen los modelos
SQLAlchemy 2.x de `serverless/lambda/shared/db/models/` (fuente de verdad,
35 tablas — CV + datos del visitante) gestionados por un solo Alembic.
El `stream_processor` escribe a las tablas del visitante via ese ORM.

Tablas relevantes al backend de tracking/contacto (normalizadas, tipadas,
con CHECK constraints):

### `contacts` (Neon)

```text
id               UUID PK (UUIDv7)
email            CITEXT NOT NULL       case-insensitive
name             TEXT NOT NULL
message          TEXT NOT NULL         -> GIN to_tsvector('spanish')
service_type     TEXT NOT NULL         CHECK in enum (6 valores)
company role budget timeline           TEXT
source_url       TEXT NOT NULL
source_subdomain TEXT NOT NULL         enum 6 niches
ip_address       INET NOT NULL         IPv4/IPv6 nativo
country          CHAR(2)               ISO 3166-1 alpha-2
user_agent       TEXT NOT NULL
turnstile_hostname TEXT NOT NULL
metadata         JSONB                 -> GIN jsonb_path_ops
created_at       TIMESTAMPTZ NOT NULL
stream_event_id  TEXT NOT NULL UNIQUE  idempotency desde el Stream
```

### `tracking_events` (Neon)

```text
session_id       UUID NOT NULL  }  parte de la PK
page_id          UUID NOT NULL  }  (UUIDv7 -> sort por tiempo)
created_at       TIMESTAMPTZ NOT NULL  -> PARTITION KEY
url path referrer  utm_* (5)
screen_res viewport
device_type      TEXT CHECK in (desktop|mobile|tablet)
browser os lang timezone
ip_address INET   country CHAR(2)   user_agent TEXT
source_subdomain TEXT NOT NULL
extra            JSONB  -> GIN jsonb_path_ops
expires_at       TIMESTAMPTZ NOT NULL   +60d (drop de particion)
stream_event_id  TEXT NOT NULL UNIQUE
PRIMARY KEY (session_id, page_id, created_at)
```

Range-particionada por mes; las particiones viejas se dropean (PG no
tiene TTL nativo — el `DELETE WHERE` masivo seria caro).

### `processed_stream_events` (Neon)

```text
event_id       TEXT PK        DynamoDB record eventID
source_table   TEXT NOT NULL  contacts|tracking
event_name     TEXT NOT NULL  INSERT|MODIFY|REMOVE
processed_at   TIMESTAMPTZ NOT NULL
```

Log de idempotencia del `stream_processor`: garantiza que reprocesar el
mismo record del Stream no duplique filas.

## 4. Por que hibrido y no una sola DB

| Solo... | Limitacion |
|---------|------------|
| DynamoDB | NoSQL no soporta window functions, joins ni agregaciones — el analytics CRM requeriria un scan completo + procesamiento en Lambda |
| Neon PG | psycopg3 cold start (~150-250ms) en cada Lambda del hot path; connection pool fragil con concurrencia |

Solucion: DynamoDB para el write rapido del hot path, Neon como replica
async para las queries analiticas. Comparativa completa y costos:
skill `neon` + skill `aws-dynamodb`.

## 5. Esquema PostgreSQL unificado

El Neon del portfolio tiene UN solo schema (35 tablas: CV + visitante)
gestionado por UN solo Alembic en `serverless/lambda/shared/db/alembic/`.
La Lambda `db` corre las migraciones. Diagrama ER completo:
[docs/diagrams/db-er.mmd](../../../docs/diagrams/db-er.mmd). Operacion de
las migraciones y branches Neon:
[.claude/rules/neon-management.md](../../rules/neon-management.md).

---

[<- 02-flujos](02-flujos.md) | [Siguiente: 04-deploy-operacion ->](04-deploy-operacion.md)
