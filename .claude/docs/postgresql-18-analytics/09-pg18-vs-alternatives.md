# PG18 vs alternativas: ClickHouse, BigQuery, TimescaleDB

> Comparacion de opciones para analytics del portfolio. Por que PG18 es correcto HOY, cuando cambiar.

**Verificado**: 2026-05-14

[← Dashboard queries](./08-queries-dashboard.md) | [README](./README.md) | [Siguiente: Gotchas →](./10-gotchas.md)

## Decision matrix: volumen x queries

```
                  Volumen esperado (rows/ano)
                  ↓
                  <100k       100k-10M        >10M
                  ↓           ↓               ↓
Latency
sensible (ms)    PG18 ✅     PG18 / TS ✅    ClickHouse ✅
Latency slow     PG18 ✅     PG18 / BQ ✅    BigQuery ✅
```

Portfolio hoy: ~200 contacts/mes + ~180k tracking events/ano = **210k rows**.
→ **PG18 es optimo ahora. TimescaleDB o ClickHouse seria overkill.**

## Tabla comparativa

| Aspecto | PostgreSQL 18 | TimescaleDB | ClickHouse | BigQuery |
|---------|---|---|---|---|
| **Tipo** | OLTP + OLAP | Time-series (PG extension) | Analytical (columnar) | Cloud analytical |
| **Volumen ideal** | <10M rows | 100M-1B rows | 1B+ rows | 100M+ rows |
| **Latency** | ms-seconds | ms | seconds | seconds |
| **Cost (portfolio)** | ~$15/mes (Neon) | ~$15/mes | >$50/mes | >$50/mes |
| **Setup** | Easy (20 min) | Easy (5 min) | Medium (1h) | Medium (auth, config) |
| **Retention** | Manual DROP | Automated | Automated | Automated |
| **Full-text search** | ✅ Native | ✅ Native | ⚠ Via plugins | ⚠ Fuzzy only |
| **Window functions** | ✅ Native | ✅ Native | ❌ (Limited) | ✅ Native |
| **JSONB fields** | ✅ Native + GIN | ✅ Via JSON | ⚠ String only | ✅ JSON type |
| **Joins** | Fast | Fast | Slow (not designed) | Fast |
| **Learning curve** | Low (SQL standard) | Low (PG + extensions) | Medium (SQL variant) | Medium (BigQuery SQL) |
| **Vendor lock** | No (open source) | No (open source) | No (open source) | Yes (Google) |

## PostgreSQL 18 (actual)

### Pros
- Standard SQL (mismo que toda empresa)
- Neon free tier para portfolio (~$15/mes pro)
- Virtual generated columns (PG18) reducen storage
- UUIDv7 nativo para PKs ordenables
- Materialized views + REFRESH CONCURRENTLY
- Full-text search en español
- JSONB + GIN indexes para fields flexibles
- Window functions completas (LAG, LEAD, RANK, ROW_NUMBER)
- No overhead adicional: ~210k rows = 50MB disk

### Cons
- No automatic retention (requiere cron job manual)
- Analytics queries con table scans > 1000 filas pueden ser lentas
- Si tracking crece a 1M+ rows/mes, indexes no bastaran

### Cuando cambiar
```
Si tracking crece a > 5M rows/ano (5x hoy):
  → Evaluar TimescaleDB o agregar read replicas de PG18
  
Si tracking crece a > 100M rows/ano (500x hoy):
  → Considerar ClickHouse o BigQuery
```

## TimescaleDB (extension de PG18)

TimescaleDB = PostgreSQL + time-series superpowers. Es PG18 + extension.

### Pros
- Super fácil instalacion: `CREATE EXTENSION timescaledb`
- Hypertable compression automatica (50% menos storage)
- Downsampling y retention policies nativas
- Chunk-based partitioning (mejor que range partitions manuales)
- Query performance ~10x mejor que PG nativo para time-series
- Same SQL como PG, window functions completas

### Cons
- Extra extension = depender de TimescaleDB updates
- Compression overhead CPU (pero recupera en storage/IO)
- Aun SQL estándar, pero con quirks de TimescaleDB

### Ejemplo: convertir a TimescaleDB

```sql
-- Step 1: Instalar (Neon no lo provee por defecto, pedirlo)
CREATE EXTENSION timescaledb;

-- Step 2: Convertir tabla a hypertable
SELECT create_hypertable('tracking_events', 'created_at');

-- Step 3: Benefit automatico
-- - Chunk-based partitioning (automatic)
-- - Compression (manual): ALTER TABLE tracking_events SET (timescaledb.compress = on);
-- - Retention: SELECT add_retention_policy('tracking_events', INTERVAL '60 days');

-- Step 4: Mismas queries, 10x mas rapido
EXPLAIN ANALYZE SELECT * FROM tracking_events
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
AND page_path = '/portfolio';
-- Plan: TimescaleDB scan (faster than B-tree)
```

### Cuando usar TimescaleDB
```
Tracking crece a 1-10M rows/ano:
  → Cambiar a TimescaleDB es 1 ALTER TABLE + compression config
  → Costo: 0 (misma factura Neon)
  → Tiempo: 30 min setup + compression
```

## ClickHouse (OLAP real)

ClickHouse = base de datos columnar especializada en analytics. **No es relacional.**

### Pros
- **Compression extreme**: 100:1 (1GB datos = 10MB disk)
- **Queries MASIVAS ultra-rapidas**: aggregates en segundos sobre billions
- **Retention automatizada**: DROP columns/tables sin costo
- **No indexes**: columnar format es optimizado per se

### Cons
- **No ACID**: inserciones eventualmente consistentes
- **No UPDATE/DELETE eficiente**: data es immutable basically
- **SQL es variant**: no window functions, CTEs limitadas, JOIN behavior distinto
- **Infraestructura**: debes hostear (ClickHouse Cloud ~$100+/mes) o self-host (Ops burden)
- **Learning curve**: queries estan optimizadas diferente que SQL estándar

### Ejemplo: migrate tracking_events

```sql
-- ClickHouse syntax (distinto!)
CREATE TABLE tracking_events (
  id String,
  created_at DateTime,
  session_id String,
  page_path String,
  utm_source Nullable(String),
  time_on_page_seconds UInt32,
  extra JSON
)
ENGINE = MergeTree()
ORDER BY (created_at, session_id)
TTL created_at + INTERVAL 60 DAY;  -- retention automatica!

-- Query (funciona, pero limitada en window functions)
SELECT
  toDate(created_at) AS date,
  COUNT(*) AS page_views
FROM tracking_events
GROUP BY date
ORDER BY date DESC;

-- Window functions NO existen
-- LAG, LEAD: NO SOPORTADO (error)
-- Workaround: usar LIMIT 1 BY session_id
SELECT *
FROM tracking_events
WHERE created_at >= CURRENT_DATE - INTERVAL 7 DAY
ORDER BY session_id, created_at
LIMIT 1 BY session_id;
```

### Cuando usar ClickHouse
```
Tracking crece a > 100M rows/ano (500x hoy):
  → Analytics queries necesitan < 1 segundo
  → No necesitas UPDATE/DELETE en datos viejos
  → Presupuesto para infraestructura: >$100/mes
```

## BigQuery (Cloud data warehouse)

BigQuery = Google's managed data warehouse. OLAP 100%, serverless.

### Pros
- **Zero ops**: sin mantenance, autoscaling, backups automaticos
- **Mega-fast**: queries en billions de rows en segundos
- **SQL casi estándar**: window functions completas, CTEs, JOINs
- **Integration**: con Google Analytics 360, looker, data studio nativamente
- **Pricing**: pay-per-query (no retention cost)

### Cons
- **Vendor lock**: datos viven en Google, export caro
- **Minimum cost**: incluso pequeñas queries salen >$6/mes
- **Para este portfolio**: overkill, waste de dinero (seria $50+/mes por sencillez)
- **Cold storage**: queries > 30 dias usan diferentes pricing (mas lento)

### Ejemplo: load tracking_events

```sql
-- BigQuery Terraform / gcloud
bq load --source_format=NEWLINE_DELIMITED_JSON \
  my_dataset.tracking_events \
  gs://my-bucket/tracking_*.json

-- Query (SQL muy similar a PG)
SELECT
  DATE(created_at) AS date,
  page_path,
  COUNT(DISTINCT session_id) AS unique_sessions,
  COUNT(*) AS page_views
FROM tracking_events
WHERE created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY date, page_path
ORDER BY date DESC, page_views DESC
LIMIT 10;
```

### Cuando usar BigQuery
```
Tracking crece a > 10B rows/ano (50000x hoy):
  → Google Cloud as central data warehouse
  → Presupuesto sin limite
  → Need realtime BI dashboards (Looker integration)
```

---

## Decision tree: que elegir ahora

```
START: Portfolio actualmente con 210k rows/ano

1. Queries son rapidas?
   SI  → Quedate con PG18 ✅
   NO  → Va a Step 2

2. Tracking va a crecer > 5M rows/ano en 2 anos?
   SI  → TimescaleDB (Step 3)
   NO  → PG18 + mejor indexing (Step 4)

3. Necesitas compression extrema + zero-cost retention?
   SI  → TimescaleDB ✅
   NO  → PG18 + cron retention (Step 4)

4. Necesitas queries en < 100ms sobre 1B rows?
   SI  → ClickHouse o BigQuery
   NO  → PG18 + materialized views ✅

5. Eres parte de Google Cloud ecosystem?
   SI  → BigQuery ✅
   NO  → ClickHouse (si presupuesto) o PG18
```

---

## Roadmap propuesto para portfolio

### Fase 1 (Ahora): PostgreSQL 18 Neon
```
- Range partitioning tracking_events (retention manual)
- Materialized views (refresh pg_cron)
- Full-text search contacts.message
- JSONB metadata (utm, device, browser)
- Estimated cost: $15/mes
```

### Fase 2 (Si tracking crece > 2M rows/ano, ~2 anos)
```
- Evaluar TimescaleDB upgrade (1 ALTER TABLE)
- Automatic compression + retention policies
- Cost: $15/mes (mismo que hoy)
- Time: 1 day migration testing
```

### Fase 3 (Si tracking crece > 50M rows/ano, ~5 anos)
```
- Decouple analytics a ClickHouse o BigQuery
- PG18 sigue siendo OLTP (contacts)
- ClickHouse/BQ es OLAP (tracking analytics)
- ETL: nightly load de tracking_aggregates a data warehouse
- Cost: PG18 ($15) + ClickHouse ($100+) o BigQuery ($50+)
```

---

## Referencias

- [PostgreSQL 18 vs TimescaleDB (Neon)](https://neon.tech/postgresql/postgresql-timescaledb-comparison)
- [ClickHouse Official Docs](https://clickhouse.com/docs)
- [BigQuery Data Warehouse (Google Cloud)](https://cloud.google.com/bigquery/docs)
- [Time-based Retention Strategies (Sequin)](https://blog.sequinstream.com/time-based-retention-strategies-in-postgres/)
