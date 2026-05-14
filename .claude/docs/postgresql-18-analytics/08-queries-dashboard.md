# 10 Dashboard queries - copy-paste ready

> Queries listas para usar en dashboard. Copiadas directamente a `SELECT` sin cambios.

**Verificado**: 2026-05-14 | **Updated**: Usa tables `contacts`, `tracking_events`, `tracking_daily_aggregates`

[← JSONB](./07-jsonb-flexible-fields.md) | [README](./README.md) | [Siguiente: PG18 alternatives →](./09-pg18-vs-alternatives.md)

## 1. Contactos nuevos por mes + niche

```sql
SELECT
  DATE_TRUNC('month', created_at)::DATE AS month,
  niche,
  COUNT(*) AS contact_count,
  COUNT(DISTINCT service_type) AS service_types,
  ROUND(AVG(LENGTH(message))::NUMERIC, 0) AS avg_message_length
FROM contacts
WHERE created_at >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', created_at), niche
ORDER BY month DESC, contact_count DESC;
```

## 2. Conversion rate (contacts / unique sessions)

```sql
WITH daily_metrics AS (
  SELECT
    DATE_TRUNC('day', c.created_at)::DATE AS date,
    COUNT(DISTINCT c.id) AS conversions,
    COUNT(DISTINCT te.session_id) AS unique_sessions
  FROM contacts c
  CROSS JOIN tracking_events te
  WHERE c.created_at >= CURRENT_DATE - INTERVAL '30 days'
    AND te.created_at >= CURRENT_DATE - INTERVAL '30 days'
  GROUP BY DATE_TRUNC('day', c.created_at)
)
SELECT
  date,
  conversions,
  unique_sessions,
  ROUND(100.0 * conversions / NULLIF(unique_sessions, 0), 2) AS conversion_rate_pct
FROM daily_metrics
ORDER BY date DESC;
```

## 3. Top 10 landing pages

```sql
WITH landing_pages AS (
  SELECT
    page_path,
    COUNT(DISTINCT session_id) AS unique_sessions,
    COUNT(*) AS page_views,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_total
  FROM tracking_events
  WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
  GROUP BY page_path
)
SELECT
  page_path,
  unique_sessions,
  page_views,
  pct_of_total,
  RANK() OVER (ORDER BY page_views DESC) AS rank
FROM landing_pages
WHERE rank <= 10
ORDER BY rank;
```

## 4. Session journey: pagina anterior -> siguiente

```sql
SELECT
  session_id,
  page_path,
  created_at,
  LAG(page_path) OVER (PARTITION BY session_id ORDER BY created_at) AS previous_page,
  LEAD(page_path) OVER (PARTITION BY session_id ORDER BY created_at) AS next_page,
  ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY created_at) AS step
FROM tracking_events
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
  AND session_id = 'YOUR_SESSION_ID_HERE'  -- Reemplaza
ORDER BY session_id, created_at;
```

## 5. Time on site por session

```sql
SELECT
  session_id,
  FIRST_VALUE(page_path) OVER (PARTITION BY session_id ORDER BY created_at) AS landing,
  LAST_VALUE(page_path) OVER (
    PARTITION BY session_id ORDER BY created_at
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
  ) AS exit,
  COUNT(*) OVER (PARTITION BY session_id) AS pages_visited,
  (MAX(created_at) OVER (PARTITION BY session_id) - 
   MIN(created_at) OVER (PARTITION BY session_id))::TEXT AS session_duration,
  MAX(created_at) OVER (PARTITION BY session_id) AS last_activity
FROM tracking_events
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY session_id, page_path, created_at
ORDER BY last_activity DESC
LIMIT 100;
```

## 6. UTM attribution: ultima campana antes de contacto

```sql
WITH session_utm AS (
  SELECT
    session_id,
    utm_source,
    utm_campaign,
    created_at,
    ROW_NUMBER() OVER (
      PARTITION BY session_id ORDER BY created_at DESC
    ) AS utm_recency
  FROM tracking_events
  WHERE utm_source IS NOT NULL
    AND created_at >= CURRENT_DATE - INTERVAL '60 days'
)
SELECT
  c.id AS contact_id,
  c.created_at AS contact_date,
  c.niche,
  c.service_type,
  COALESCE(su.utm_source, 'direct') AS utm_source,
  COALESCE(su.utm_campaign, 'organic') AS utm_campaign,
  (c.created_at - COALESCE(su.created_at, c.created_at))::TEXT AS time_since_utm,
  RANK() OVER (ORDER BY c.created_at DESC) AS recency_rank
FROM contacts c
LEFT JOIN session_utm su ON (
  CAST(c.metadata->>'session_id' AS VARCHAR) = su.session_id
  AND su.utm_recency = 1
)
WHERE c.created_at >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY c.created_at DESC;
```

## 7. Bounce rate por niche

```sql
WITH session_depth AS (
  SELECT
    session_id,
    COUNT(*) AS pages_in_session
  FROM tracking_events
  WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
  GROUP BY session_id
),
niche_sessions AS (
  SELECT
    c.niche,
    sd.session_id,
    sd.pages_in_session,
    CASE WHEN sd.pages_in_session = 1 THEN 1 ELSE 0 END AS is_bounce
  FROM tracking_events te
  LEFT JOIN contacts c ON (
    CAST(c.metadata->>'session_id' AS VARCHAR) = te.session_id
  )
  JOIN session_depth sd ON te.session_id = sd.session_id
  WHERE te.created_at >= CURRENT_DATE - INTERVAL '30 days'
)
SELECT
  niche,
  COUNT(DISTINCT session_id) AS total_sessions,
  SUM(is_bounce) AS bounce_count,
  ROUND(100.0 * SUM(is_bounce) / COUNT(DISTINCT session_id), 2) AS bounce_rate_pct
FROM niche_sessions
WHERE niche IS NOT NULL
GROUP BY niche
ORDER BY bounce_rate_pct DESC;
```

## 8. Device breakdown (mobile vs desktop)

```sql
SELECT
  CASE
    WHEN (extra->>'device')::TEXT ILIKE '%mobile%' THEN 'Mobile'
    WHEN (extra->>'device')::TEXT ILIKE '%tablet%' THEN 'Tablet'
    ELSE 'Desktop'
  END AS device_type,
  COUNT(*) AS page_views,
  COUNT(DISTINCT session_id) AS unique_sessions,
  ROUND(AVG(time_on_page_seconds)::NUMERIC, 1) AS avg_time_on_page,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_traffic
FROM tracking_events
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY device_type
ORDER BY page_views DESC;
```

## 9. Country distribution (si tienes ip_address -> country)

```sql
SELECT
  (extra->>'country')::TEXT AS country,
  COUNT(*) AS page_views,
  COUNT(DISTINCT session_id) AS unique_sessions,
  COUNT(DISTINCT CAST(extra->>'session_id' AS UUID)) AS contacts_from_country,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_traffic
FROM tracking_events
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
  AND (extra->>'country') IS NOT NULL
GROUP BY (extra->>'country')
ORDER BY page_views DESC
LIMIT 15;
```

## 10. Heatmap: horas del dia que generan contactos

```sql
SELECT
  EXTRACT(HOUR FROM created_at)::INT AS hour_of_day,
  COUNT(*) AS contact_count,
  STRING_AGG(DISTINCT niche, ', ' ORDER BY niche) AS niches,
  ROUND(
    100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
    2
  ) AS pct_of_daily_contacts
FROM contacts
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY EXTRACT(HOUR FROM created_at)
ORDER BY hour_of_day;

-- Resultado esperado:
-- hour_of_day | contact_count | niches | pct_of_daily_contacts
-- 8           | 12            | fintech, generic | 6.00
-- 9           | 18            | generic, architect | 9.00
-- 10          | 22            | fintech, leader | 11.00
-- ...
```

---

## Tips para adaptarlas

### Cambiar rango de fechas
```sql
-- De: CURRENT_DATE - INTERVAL '30 days'
-- A:  CURRENT_DATE - INTERVAL '7 days'    (ultima semana)
--     CURRENT_DATE - INTERVAL '1 year'    (ultimo ano)
--     '2026-05-01'::DATE                   (fecha especifica)
```

### Filtrar por niche
```sql
-- Agregar WHERE
WHERE c.created_at >= CURRENT_DATE - INTERVAL '30 days'
  AND c.niche = 'fintech'  -- Solo fintech
```

### Filtrar por device
```sql
-- En queries con tracking_events
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
  AND (extra->>'device') = 'mobile'
```

### Sorted/Ranked
```sql
-- Para top N, usa RANK() o ROW_NUMBER()
SELECT
  ...,
  RANK() OVER (ORDER BY metric DESC) AS rank
FROM (...)
WHERE rank <= 10;  -- Top 10
```

---

## Performance: cuales queries son lentas?

| Query | Tipo | Speed | Notas |
|-------|------|-------|-------|
| 1. Por mes + niche | Aggregation | ~500ms | Accede 6 meses, indexes OK |
| 2. Conversion rate | JOIN | ~2s | CROSS JOIN puede ser lento sin WHERE |
| 3. Top 10 landing | Aggregation | ~1s | Partitions help (7-30 dias) |
| 4. Session journey | Window | ~500ms | Requiere session_id filtr |
| 5. Time on site | Window | ~800ms | ROWS BETWEEN slicing |
| 6. UTM attribution | LEFT JOIN | ~1.5s | Depende de cardinalidad session |
| 7. Bounce rate | CTE + Agg | ~1.5s | CTE materializado |
| 8. Device breakdown | Aggregation | ~700ms | ILIKE lento si sin index |
| 9. Country dist. | Aggregation | ~1s | Depende si country en extra |
| 10. Heatmap | GROUP BY + AGG | ~600ms | Simple, rapida |

**Optimizar queries lentas**: Agregar indexes en partition key (created_at), usar materialized views para datos historicos.

---

## Exportar a CSV para analisis externo

```sql
-- Desde psql
\copy (SELECT * FROM contacts WHERE created_at >= '2026-05-01') TO '/tmp/contacts_may.csv' WITH CSV HEADER;

-- Desde Python
import psycopg
import csv

with psycopg.connect(...) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT ... FROM contacts WHERE ...")
        with open('export.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerow([desc[0] for desc in cur.description])  # header
            writer.writerows(cur.fetchall())
```

---

## Referencias

- [PostgreSQL Window Functions](https://www.postgresql.org/docs/current/functions-window.html)
- [PostgreSQL CTEs (WITH Queries)](https://www.postgresql.org/docs/current/queries-with.html)
- [PostgreSQL Date/Time Functions](https://www.postgresql.org/docs/current/functions-datetime.html)
