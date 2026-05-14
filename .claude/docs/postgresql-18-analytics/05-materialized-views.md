# Materialized views + scheduled refresh

> Como pre-computar agregaciones con materialized views y refreshearlas sin bloquear lectores.

**Verificado**: 2026-05-14

[← Window functions](./04-window-functions-analytics.md) | [README](./README.md) | [Siguiente: Partitioning →](./06-partitioning-tracking.md)

## Concepto: View vs Materialized View

| Aspecto | View | Materialized View |
|--------|------|-------------------|
| Storage | NONE (query virtual) | SI (tabla fisica) |
| Freshness | Always current | Stale (hasta refresh) |
| Query speed | Slow (query cada vez) | Fast (read from disk) |
| Update overhead | None | Hay REFRESH cost |

Para analytics con lectura frecuente, **Materialized View** es mejor.

## Vista 1: Contactos por mes + niche

```sql
CREATE MATERIALIZED VIEW mv_contacts_by_month_niche AS
SELECT
  DATE_TRUNC('month', created_at)::DATE AS month,
  niche,
  COUNT(*) AS contact_count,
  COUNT(DISTINCT service_type) AS service_types,
  MAX(created_at) AS latest_contact
FROM contacts
GROUP BY DATE_TRUNC('month', created_at), niche
ORDER BY month DESC, contact_count DESC;

-- Crear index para queries rapidas
CREATE INDEX idx_mv_contacts_month_niche ON mv_contacts_by_month_niche(month, niche);
```

**Query tipica**:
```sql
SELECT * FROM mv_contacts_by_month_niche
WHERE month >= '2026-03-01'
ORDER BY month DESC, contact_count DESC;
```

## Vista 2: Top pages por semana

```sql
CREATE MATERIALIZED VIEW mv_top_pages_weekly AS
WITH weekly_agg AS (
  SELECT
    DATE_TRUNC('week', created_at)::DATE AS week,
    page_path,
    COUNT(*) AS page_views,
    COUNT(DISTINCT session_id) AS unique_sessions,
    ROUND(AVG(time_on_page_seconds), 2) AS avg_time_on_page
  FROM tracking_events
  WHERE created_at >= CURRENT_DATE - INTERVAL '12 weeks'
  GROUP BY DATE_TRUNC('week', created_at), page_path
)
SELECT
  week,
  page_path,
  page_views,
  unique_sessions,
  avg_time_on_page,
  RANK() OVER (PARTITION BY week ORDER BY page_views DESC) AS rank_by_views
FROM weekly_agg
ORDER BY week DESC, page_views DESC;

CREATE INDEX idx_mv_top_pages_week ON mv_top_pages_weekly(week, rank_by_views);
```

**Query tipica**:
```sql
SELECT week, page_path, page_views
FROM mv_top_pages_weekly
WHERE week = CURRENT_DATE - INTERVAL '1 week'
  AND rank_by_views <= 10;
```

## Vista 3: Conversion attribution por UTM

```sql
CREATE MATERIALIZED VIEW mv_utm_attribution AS
WITH utm_contacts AS (
  SELECT
    DATE_TRUNC('day', c.created_at)::DATE AS date,
    CAST(c.metadata->>'utm_source' AS VARCHAR) AS utm_source,
    CAST(c.metadata->>'utm_campaign' AS VARCHAR) AS utm_campaign,
    c.niche,
    COUNT(*) AS conversion_count
  FROM contacts c
  WHERE c.metadata IS NOT NULL
    AND c.metadata->>'utm_source' IS NOT NULL
  GROUP BY DATE_TRUNC('day', c.created_at), 
           c.metadata->>'utm_source',
           c.metadata->>'utm_campaign',
           c.niche
)
SELECT
  date,
  utm_source,
  utm_campaign,
  niche,
  conversion_count,
  SUM(conversion_count) OVER (
    PARTITION BY utm_source ORDER BY date
  ) AS cumulative_conversions
FROM utm_contacts
ORDER BY date DESC, conversion_count DESC;

CREATE INDEX idx_mv_utm_date ON mv_utm_attribution(date, utm_source);
```

## REFRESH MATERIALIZED VIEW (opciones)

### Opcion 1: REFRESH simple (bloquea lectores)

```sql
REFRESH MATERIALIZED VIEW mv_contacts_by_month_niche;
-- Lectores: ❌ Bloqueados (2-5 segundos mientras se recalcula)
```

### Opcion 2: REFRESH CONCURRENTLY (NO bloquea)

Requisito: **UNIQUE INDEX** en la view.

```sql
-- Step 1: Agregar unique index (solo 1 permitido)
CREATE UNIQUE INDEX idx_mv_contacts_unique ON mv_contacts_by_month_niche(month, niche);

-- Step 2: Refresh sin bloquear
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_contacts_by_month_niche;
-- Resultado: Lectores siguen viendo datos viejos hasta que refresh termine
-- Tiempo: ~5-10 segundos (mas lento que REFRESH normal por sincronizacion)
```

## Scheduling con pg_cron (Neon compatible)

Neon soporta la extension `pg_cron` para scheduled tasks. Verificar:

```sql
-- Verificar que pg_cron esta disponible
SELECT * FROM pg_available_extensions WHERE name = 'pg_cron';

-- Si no esta, crear:
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Ver jobs actuales
SELECT * FROM cron.job;
```

### Programar refreshes diarios

```sql
-- Refresh de mv_contacts_by_month_niche a la 1 AM UTC
SELECT cron.schedule(
  'refresh_contacts_by_month_niche',  -- job_name
  '0 1 * * *',                        -- cron syntax: 1 AM every day
  'REFRESH MATERIALIZED VIEW CONCURRENTLY mv_contacts_by_month_niche'
);

-- Refresh de mv_top_pages_weekly (lunes a las 2 AM)
SELECT cron.schedule(
  'refresh_top_pages_weekly',
  '0 2 * * 1',                        -- 1 = lunes (0 = domingo)
  'REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_pages_weekly'
);

-- Refresh de mv_utm_attribution (diario a las 3 AM)
SELECT cron.schedule(
  'refresh_utm_attribution',
  '0 3 * * *',
  'REFRESH MATERIALIZED VIEW CONCURRENTLY mv_utm_attribution'
);
```

### Ver y desactivar jobs

```sql
-- Listar todos los jobs
SELECT job_id, jobname, schedule, command FROM cron.job;

-- Desactivar un job (sin borrar)
SELECT cron.unschedule('refresh_contacts_by_month_niche');

-- Borrar un job
SELECT cron.unschedule(job_id) FROM cron.job 
WHERE jobname = 'refresh_contacts_by_month_niche';
```

## Alternative: Lambda cron external

Si prefieres NO depender de pg_cron (Neon puede deprecarlo), usa Lambda external:

```python
# Lambda function (on schedule: EventBridge daily at 1 AM UTC)
import psycopg
import os

def handler(event, context):
    conn_str = os.environ['DATABASE_URL']
    conn = psycopg.connect(conn_str)
    
    views = [
        'mv_contacts_by_month_niche',
        'mv_top_pages_weekly',
        'mv_utm_attribution',
    ]
    
    for view in views:
        try:
            conn.execute(
                f'REFRESH MATERIALIZED VIEW CONCURRENTLY {view}'
            )
            print(f'Refreshed {view}')
        except Exception as e:
            print(f'Error refreshing {view}: {e}')
    
    conn.commit()
    conn.close()
    
    return {'statusCode': 200, 'body': 'Refreshes complete'}
```

## Monitoreo de materialized views

### Ver size y freshness

```sql
SELECT
  matviewname,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) AS size,
  (NOW() - MAX(f.created_at))::TEXT AS time_since_refresh
FROM pg_matviews mv
LEFT JOIN contacts f ON TRUE  -- dummy join to get timestamp
WHERE mv.schemaname = 'public'
GROUP BY mv.matviewname;

-- Mejor: guardar timestamp de refresh en tabla separada
CREATE TABLE _mv_refresh_log (
  view_name VARCHAR(255),
  last_refresh_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agregar trigger a cada view (pseudocodigo)
-- Despues de REFRESH CONCURRENTLY, update la tabla
```

### Ver queries lentas

```sql
-- Queries en views que toman > 1s
EXPLAIN ANALYZE
SELECT * FROM mv_contacts_by_month_niche
WHERE month >= CURRENT_DATE - INTERVAL '1 month';
-- Si cost > 1000, ajusta la query (agregar indexes, cambiar aggregate)
```

## Best practices

1. **Una unica unique index** para CONCURRENTLY:
   ```sql
   CREATE UNIQUE INDEX idx_mv_contacts_unique ON mv_contacts_by_month_niche(month, niche);
   -- Si tienes 2+ unique indexes, CONCURRENTLY falla
   ```

2. **Schedule refreshes en horarios bajos**:
   - 1-3 AM UTC es tipicamente bajo trafico
   - Portfolio es CMS personal, no e-commerce, asi que timing flexible

3. **Evitar refresh durante inserciones masivas**:
   - Si Lambda processor hace batch inserts a las 12:30 AM, schedule refresh a las 2 AM
   - Neon puede aumentar locks si ambos ocurren simultaneamente

4. **Monitoring: alertar si refresh falla**:
   ```python
   # En Lambda post-refresh
   if refresh_status == 'ERROR':
       send_alert(f'MV refresh failed: {error_msg}')
   ```

---

## Ejemplo completo: dashboard queries

```sql
-- Dashboard home: ultimos 30 dias
SELECT * FROM mv_contacts_by_month_niche
WHERE month >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY month DESC;

-- Top 10 paginas de esta semana
SELECT page_path, page_views, unique_sessions
FROM mv_top_pages_weekly
WHERE week = (SELECT MAX(week) FROM mv_top_pages_weekly)
  AND rank_by_views <= 10;

-- Conversions por source esta semana
SELECT utm_source, SUM(conversion_count) AS total
FROM mv_utm_attribution
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY utm_source
ORDER BY total DESC;
```

---

## Referencias

- [PostgreSQL Materialized Views](https://www.postgresql.org/docs/current/sql-refreshmaterializedview.html)
- [pg_cron: Job Scheduling (Neon)](https://neon.tech/docs/extensions/pg_cron)
- [REFRESH MATERIALIZED VIEW CONCURRENTLY (Gold Lapel)](https://goldlapel.com/glossary/postgres/refresh-materialized-view-concurrently)
