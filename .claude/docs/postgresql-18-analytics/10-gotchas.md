# Gotchas + troubleshooting

> Errores comunes, timezone issues, query debugging, performance tips.

**Verificado**: 2026-05-14

[← PG18 alternatives](./09-pg18-vs-alternatives.md) | [README](./README.md)

## Timezone issues (CRITICAL)

PostgreSQL por defecto usa **UTC** internamente. Pero Neon puede variar.

### Problema: Queries "ultimos 7 dias" retornan datos erroneos

```sql
-- MALO: asume CURRENT_DATE en tu zona, no UTC
SELECT COUNT(*) FROM tracking_events
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days';
-- Si eres en CL (UTC-3), esta query busca desde hace 4 horas, no 7 dias!

-- BIEN: explicito en UTC
SELECT COUNT(*) FROM tracking_events
WHERE created_at >= (NOW() AT TIME ZONE 'UTC')::DATE - INTERVAL '7 days';

-- O mejor aun: storage en UTC, conversion al final
SELECT COUNT(*) FROM tracking_events
WHERE created_at >= CURRENT_DATE::TIMESTAMP AT TIME ZONE 'UTC' - INTERVAL '7 days';
```

### Verificar timezone de la base de datos

```sql
SHOW timezone;
-- Resultado: Etc/UTC (ideal)

-- Si es diferente:
SET timezone = 'UTC';
ALTER DATABASE portfolio SET timezone = 'UTC';
```

### Insertar datos con timezone explicito

```python
# Python / psycopg3 - BIEN
from datetime import datetime, timezone
import psycopg

now_utc = datetime.now(timezone.utc)

conn.execute("""
  INSERT INTO contacts (created_at, ...) VALUES (%s, ...)
""", (now_utc, ...))
# psycopg3 traduce automaticamente a TIMESTAMP WITH TIME ZONE
```

---

## Partitioning gotchas

### Problema: INSERT falla con "no partition found"

```sql
-- Crear partition solo para 2026-01 a 2026-03
CREATE TABLE tracking_events_2026_01 PARTITION OF tracking_events
  FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- INSERT en 2026-05 falla:
INSERT INTO tracking_events (created_at, ...) 
VALUES (NOW(), ...);
-- ERROR: no partition found for created_at = '2026-05-14'
```

**Solucion**: Crear partitions for future
```sql
-- Agregar partitions futuras
CREATE TABLE tracking_events_2026_04 PARTITION OF tracking_events
  FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
CREATE TABLE tracking_events_2026_05 PARTITION OF tracking_events
  FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
CREATE TABLE tracking_events_2026_06 PARTITION OF tracking_events
  FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
```

### Problema: Index hereda pero no se crea en nuevas partitions

```sql
-- CREATE INDEX en parent, pero nueva partition creada manualmente
CREATE TABLE tracking_events_2026_06 PARTITION OF tracking_events
  FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');

-- Index NO aparece en esta partition
SELECT * FROM pg_indexes WHERE tablename = 'tracking_events_2026_06';
-- Empty result!
```

**Solucion**: Crear index DESPUES de la partition
```sql
-- Option 1: Manualmente en partition hijo
CREATE INDEX idx_tracking_2026_06_created_at ON tracking_events_2026_06(created_at DESC);

-- Option 2: Recrear index en parent (se hereda en hijas existing)
DROP INDEX CONCURRENTLY idx_tracking_created_at;
CREATE INDEX CONCURRENTLY idx_tracking_created_at ON tracking_events(created_at DESC);
-- Solo se hereda en partitions creadas despues
```

---

## JSONB gotchas

### Problema: `->` devuelve JSONB, `->>` devuelve TEXT

```sql
-- MALO: comparar tipo erroneo
SELECT COUNT(*) FROM contacts
WHERE metadata->'device' = 'mobile';  -- Comparas JSONB con STRING → FALSE

-- BIEN: usar ->>
SELECT COUNT(*) FROM contacts
WHERE metadata->>'device' = 'mobile';  -- TEXT = TEXT → TRUE
```

### Problema: GIN index no se usa en query

```sql
-- Index existe
CREATE INDEX idx_contacts_metadata ON contacts USING GIN (metadata jsonb_path_ops);

-- Pero query no lo usa
EXPLAIN ANALYZE
SELECT COUNT(*) FROM contacts
WHERE metadata->>'device' = 'mobile';
-- Plan: Seq Scan (no usa index!)

-- Solucion: usa @> en lugar de ->>
EXPLAIN ANALYZE
SELECT COUNT(*) FROM contacts
WHERE metadata @> '{"device": "mobile"}';
-- Plan: Index Scan on idx_contacts_metadata (uses index!)
```

### Problema: NULL values en JSONB

```sql
-- metadata EXISTE pero la key NO
INSERT INTO contacts (email, metadata)
VALUES ('test@example.com', '{"utm_source": "email"}'::JSONB);

-- Query para devices
SELECT metadata->>'device' FROM contacts;
-- Resultado: NULL (key doesnt exist)

-- Filter por existence
SELECT COUNT(*) FROM contacts
WHERE metadata->>'device' IS NOT NULL;
-- Resultado: 0 (no devices definidos)

-- Better: usar ? operador
SELECT COUNT(*) FROM contacts
WHERE metadata ? 'device';
-- Resultado: 0 (key doesnt exist)
```

---

## Query performance issues

### Problema: Query toma 10+ segundos

```sql
-- LENTO: table scan total (sin WHERE)
SELECT COUNT(*) FROM tracking_events;
-- Seq Scan on tracking_events (rows=180000)

-- MEJOR: agrega WHERE con partition key
SELECT COUNT(*) FROM tracking_events
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';
-- Index Scan (prunes 11/12 partitions, scans 1 partition)
```

### Problema: DISTINCT es lento

```sql
-- LENTO: collecta TODAS las filas, luego distinct
SELECT DISTINCT session_id FROM tracking_events;
-- Hash Aggregate (rows=50000) - 5+ segundos

-- MEJOR: si quieres conteo
SELECT COUNT(DISTINCT session_id) FROM tracking_events
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';
-- Aggregate (rows=2000) - 500ms
```

### Problema: Joins con bad cardinality

```sql
-- LENTO: cross join accidental
SELECT c.id, te.session_id
FROM contacts c
CROSS JOIN tracking_events te;
-- Result: 210k * 180k = 37B rows (memory boom)

-- Siempre agrega WHERE
SELECT c.id, te.session_id
FROM contacts c
LEFT JOIN tracking_events te ON (
  CAST(c.metadata->>'session_id' AS VARCHAR) = te.session_id
  AND te.created_at >= c.created_at - INTERVAL '30 days'
);
```

---

## Materialized view gotchas

### Problema: REFRESH CONCURRENTLY requiere UNIQUE index

```sql
-- View creado
CREATE MATERIALIZED VIEW mv_contacts_by_month AS ...;

-- REFRESH CONCURRENTLY falla
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_contacts_by_month;
-- ERROR: cannot refresh materialized view concurrently without unique index

-- Solucion: agregar unique index
CREATE UNIQUE INDEX idx_mv_contacts_unique ON mv_contacts_by_month(month);
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_contacts_by_month;  -- OK
```

### Problema: View read es muy lento (view es "stale")

```sql
-- View fue creado hace 24 horas, datos nuevos no estan
SELECT * FROM mv_contacts_by_month
WHERE month = CURRENT_DATE::DATE;
-- Resultado: old data

-- Solucion: refresh manual primero
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_contacts_by_month;
SELECT * FROM mv_contacts_by_month
WHERE month = CURRENT_DATE::DATE;
-- Resultado: fresh data
```

---

## Connection + Auth gotchas

### Problema: Connection timeout de Neon

```
Error: connect ETIMEDOUT 203.0.113.1:5432
```

**Causes**:
- Firewall bloqueando PostgreSQL
- Connection pooling exhausted (Neon free tier ~100 connections)
- Network latency (Lambda en diferente region que Neon)

**Solucion**:
```python
# Usar connection pooling (PgBouncer) o reducir conexiones
import psycopg
from psycopg import pool

# Connection pool reusable
conn_pool = pool.SimpleConnectionPool(
  1,  # min connections
  10, # max connections
  "postgresql://user:password@neon-endpoint/portfolio"
)

def get_connection():
  return conn_pool.getconn()

def return_connection(conn):
  conn_pool.putconn(conn)
```

### Problema: SSL certificate mismatch

```
Error: SSL: CERTIFICATE_VERIFY_FAILED
```

**Solucion**:
```python
import psycopg
import ssl

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = True
ssl_context.verify_mode = ssl.CERT_REQUIRED

conn = psycopg.connect(
  "postgresql://...",
  ssl=ssl_context
)

# O: disable verificacion (solo dev!)
conn = psycopg.connect(
  "postgresql://...",
  sslmode='require'  # SSL required but not verified
)
```

---

## Lambda processor gotchas

### Problema: Lambda timeout durante REFRESH MATERIALIZED VIEW

```
Task timed out after 15 seconds
```

**Solucion**: Aumentar timeout + schedule cron separado
```python
# Option 1: Increase timeout (Lambda max 15 min)
# En AWS Lambda config: Timeout = 60 seconds

# Option 2: Schedule en pg_cron, no en Lambda
SELECT cron.schedule(
  'refresh_mv_daily',
  '0 2 * * *',
  'REFRESH MATERIALIZED VIEW CONCURRENTLY mv_contacts_by_month_niche'
);

# Lambda simplemente hace INSERT, no refresh
```

### Problema: Transaction bloqueada esperando partition DROP

```python
# Lambda intenta DROP partition mientras INSERT ocurre
# → Deadlock

# Solucion: usar NOWAIT
conn.execute("DROP TABLE IF EXISTS tracking_events_2026_01 NOWAIT")
# Si hay lock, falla inmediatamente en lugar de esperar
```

---

## Debug: EXPLAIN ANALYZE

```sql
-- Ver plan de ejecucion
EXPLAIN ANALYZE
SELECT COUNT(*) FROM tracking_events
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
  AND page_path = '/portfolio';

-- Output esperado:
--  Seq Scan on tracking_events_2026_05  (cost=0.00..15.00 rows=50)
--    Filter: (created_at >= ...) AND (page_path = '/portfolio')
--  Planning Time: 0.500 ms
--  Execution Time: 5.200 ms

-- Si tiempo es > 1000ms, agregar index:
CREATE INDEX idx_tracking_date_page ON tracking_events(created_at, page_path);
REINDEX INDEX CONCURRENTLY idx_tracking_date_page;
```

---

## Monitoreo + alerting

### Ver queries lentas

```sql
-- Ver top 10 queries por tiempo total
SELECT
  query,
  calls,
  mean_exec_time,
  total_exec_time
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- Resetear stats
SELECT pg_stat_statements_reset();
```

### Alertar si partition no existe

```python
# Lambda pre-flight check
import psycopg

def check_partition_exists(conn, year_month):
  partition_name = f"tracking_events_{year_month}"
  result = conn.execute("""
    SELECT EXISTS(
      SELECT 1 FROM pg_tables
      WHERE tablename = %s
    )
  """, (partition_name,)).fetchone()
  
  if not result[0]:
    # Create partition or raise alert
    raise Exception(f"Partition {partition_name} missing!")
```

---

## Checklist: antes de produccion

- [ ] Timezone = UTC explicitamente seteado
- [ ] Partitions creadas 2 meses forward
- [ ] All indexes CONCURRENTLY creados
- [ ] Materialized views tienen UNIQUE index
- [ ] pg_cron jobs scheduled (o Lambda alternatives)
- [ ] Connection pooling configurado
- [ ] EXPLAIN ANALYZE OK en queries frecuentes (< 1000ms)
- [ ] Backup policy definida (Neon automatic)
- [ ] Monitoring del `pg_stat_statements` setup
- [ ] Lambda timeout >= 60 seconds
- [ ] SSL certificado valido

---

## Referencias

- [PostgreSQL EXPLAIN ANALYZE](https://www.postgresql.org/docs/current/sql-explain.html)
- [Neon Connection Pooling](https://neon.tech/docs/guides/connection-pooling)
- [PostgreSQL Timezone Handling](https://www.postgresql.org/docs/current/datatype-datetime.html)
