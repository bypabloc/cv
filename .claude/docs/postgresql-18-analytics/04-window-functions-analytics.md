# Window functions para analytics

> Como usar LAG, LEAD, ROW_NUMBER, RANK y PARTITION BY para reconstruir session journeys, calcular metricas por grupo, y detectar anomalias.

**Verificado**: 2026-05-14

[← Indexes](./03-indexes-strategy.md) | [README](./README.md) | [Siguiente: Materialized views →](./05-materialized-views.md)

## Concepto base: PARTITION BY + ORDER BY

Window functions operan sobre un "frame" de rows, no toda la tabla.

```sql
-- Window function basica
SELECT
  session_id,
  page_path,
  created_at,
  ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY created_at) AS page_sequence
FROM tracking_events
ORDER BY session_id, created_at;

-- Resultado esperado (session ABC):
-- session_id | page_path      | created_at           | page_sequence
-- ABC        | /portfolio     | 2026-05-14 10:00:00 | 1
-- ABC        | /experience    | 2026-05-14 10:05:00 | 2
-- ABC        | /projects      | 2026-05-14 10:10:00 | 3
-- ABC        | /contact       | 2026-05-14 10:15:00 | 4
```

## Caso 1: Session Journey (LAG + LEAD)

**Pregunta**: "¿Cuales son las paginas que PRECEDEN a un contacto?"

```sql
SELECT
  session_id,
  page_path,
  created_at,
  LAG(page_path) OVER (PARTITION BY session_id ORDER BY created_at) AS previous_page,
  LEAD(page_path) OVER (PARTITION BY session_id ORDER BY created_at) AS next_page,
  ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY created_at) AS page_num
FROM tracking_events
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY session_id, created_at;

-- Resultado:
-- session_id | page_path      | previous_page  | next_page      | page_num
-- ABC        | /portfolio     | NULL           | /experience    | 1
-- ABC        | /experience    | /portfolio     | /projects      | 2
-- ABC        | /projects      | /experience    | /contact       | 3
-- ABC        | /contact       | /projects      | NULL           | 4
```

**Use case**: Entender funnel: "¿Que paginas antes de un contacto generan conversion?"

## Caso 2: Landing + Exit page (FIRST_VALUE + LAST_VALUE)

**Pregunta**: "Primera y ultima pagina por session"

```sql
SELECT DISTINCT
  session_id,
  FIRST_VALUE(page_path) OVER (
    PARTITION BY session_id ORDER BY created_at
  ) AS landing_page,
  LAST_VALUE(page_path) OVER (
    PARTITION BY session_id 
    ORDER BY created_at
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
  ) AS exit_page,
  COUNT(*) OVER (PARTITION BY session_id) AS pages_viewed,
  MAX(created_at) OVER (PARTITION BY session_id) - MIN(created_at) OVER (PARTITION BY session_id) AS session_duration
FROM tracking_events
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY session_id;

-- Resultado:
-- session_id | landing_page  | exit_page      | pages_viewed | session_duration
-- ABC        | /portfolio    | /contact       | 4            | 15 minutes
-- DEF        | /fintech      | /projects      | 2            | 5 minutes
-- GHI        | /generic      | /generic       | 1            | 0 seconds
```

**Use case**: Bounce rate (pages_viewed = 1), landing page optimization.

## Caso 3: Conversion attribution (UTM tracking)

**Pregunta**: "¿Cual fue la ULTIMA campana (utm_source) antes de cada contacto?"

```sql
-- Step 1: Traer ultimo utm_source de cada sesion
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
)
-- Step 2: Joinear con contactos
SELECT
  c.id AS contact_id,
  c.created_at AS contact_date,
  c.niche,
  su.utm_source,
  su.utm_campaign,
  (c.created_at - su.created_at) AS time_since_utm
FROM contacts c
LEFT JOIN session_utm su ON (
  c.ip_address = (
    -- Oops, contacts no tiene ip_address!
    -- Solution: guardar en metadata JSONB
    SELECT CAST(c.metadata->>'ip' AS INET)
  )
  AND su.utm_recency = 1
)
WHERE c.created_at >= CURRENT_DATE - INTERVAL '30 days';

-- Mejor approach: usar session_id en contacts.metadata
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
)
SELECT
  c.id AS contact_id,
  c.created_at,
  c.niche,
  su.utm_source,
  su.utm_campaign,
  (c.created_at - su.created_at)::TEXT AS time_since_utm
FROM contacts c
LEFT JOIN session_utm su ON (
  CAST(c.metadata->>'session_id' AS VARCHAR) = su.session_id
  AND su.utm_recency = 1
)
WHERE c.created_at >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY c.created_at DESC;
```

**Use case**: Attribution report: "cuales campanas traen conversiones reales".

## Caso 4: Time-on-page + Engagement metrics

**Pregunta**: "¿Cual es el promedio de tiempo en pagina por device?"

```sql
SELECT
  DATE_TRUNC('day', created_at)::DATE AS date,
  page_path,
  (extra->>'device') AS device,
  COUNT(*) AS page_views,
  AVG(time_on_page_seconds) AS avg_time_on_page,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY time_on_page_seconds) AS median_time,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY time_on_page_seconds) AS p95_time
FROM tracking_events
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE_TRUNC('day', created_at), page_path, extra->>'device'
ORDER BY date DESC, page_views DESC;

-- Resultado:
-- date       | page_path      | device | page_views | avg_time_on_page | median_time | p95_time
-- 2026-05-14 | /portfolio     | mobile | 250        | 45               | 32          | 180
-- 2026-05-14 | /portfolio     | desktop| 320        | 62               | 52          | 220
-- 2026-05-14 | /experience    | mobile | 150        | 38               | 25          | 140
```

**Use case**: Mobile optimization: ¿mobile tiene engagement peor?

## Caso 5: Bounce rate por landing page

**Pregunta**: "¿Cuales paginas tienen bounce rate alto?"

```sql
WITH session_stats AS (
  SELECT
    session_id,
    FIRST_VALUE(page_path) OVER (
      PARTITION BY session_id ORDER BY created_at
    ) AS landing_page,
    COUNT(*) OVER (PARTITION BY session_id) AS pages_in_session
  FROM tracking_events
  WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
)
SELECT
  landing_page,
  COUNT(DISTINCT session_id) AS total_sessions,
  SUM(CASE WHEN pages_in_session = 1 THEN 1 ELSE 0 END) AS bounced_sessions,
  ROUND(
    100.0 * SUM(CASE WHEN pages_in_session = 1 THEN 1 ELSE 0 END) / COUNT(DISTINCT session_id),
    2
  ) AS bounce_rate_pct
FROM session_stats
GROUP BY landing_page
ORDER BY bounce_rate_pct DESC;

-- Resultado:
-- landing_page | total_sessions | bounced_sessions | bounce_rate_pct
-- /generic     | 450            | 180              | 40.0
-- /vibe        | 120            | 30               | 25.0
-- /fintech     | 280            | 56               | 20.0
```

**Use case**: Entender que niches generan engagement, que paginas necesitan optimizacion.

## Caso 6: Ranking de conversiones por niche

**Pregunta**: "Top 5 niches por numero de conversiones"

```sql
WITH niche_conversions AS (
  SELECT
    c.niche,
    COUNT(c.id) AS conversion_count,
    RANK() OVER (ORDER BY COUNT(c.id) DESC) AS rank
  FROM contacts c
  WHERE c.created_at >= CURRENT_DATE - INTERVAL '30 days'
  GROUP BY c.niche
)
SELECT
  rank,
  niche,
  conversion_count
FROM niche_conversions
WHERE rank <= 5
ORDER BY rank;

-- Resultado:
-- rank | niche      | conversion_count
-- 1    | generic    | 85
-- 2    | fintech    | 32
-- 3    | architect  | 28
-- 4    | leader     | 15
-- 5    | vibe       | 10
```

## Caso 7: MoM growth (Month-over-Month)

**Pregunta**: "¿Como crecemos mes a mes?"

```sql
WITH monthly_stats AS (
  SELECT
    DATE_TRUNC('month', created_at)::DATE AS month,
    COUNT(*) AS contact_count
  FROM contacts
  GROUP BY DATE_TRUNC('month', created_at)
)
SELECT
  month,
  contact_count,
  LAG(contact_count) OVER (ORDER BY month) AS prev_month,
  contact_count - LAG(contact_count) OVER (ORDER BY month) AS absolute_change,
  ROUND(
    100.0 * (contact_count - LAG(contact_count) OVER (ORDER BY month)) / 
    LAG(contact_count) OVER (ORDER BY month),
    2
  ) AS pct_change
FROM monthly_stats
ORDER BY month;

-- Resultado:
-- month      | contact_count | prev_month | absolute_change | pct_change
-- 2026-03-01 | 95            | NULL       | NULL            | NULL
-- 2026-04-01 | 140           | 95         | 45              | 47.37
-- 2026-05-01 | 195           | 140        | 55              | 39.29
```

---

## Performance Tips

1. **Particion pequena**: PARTITION BY session_id es rapido (session 1000s de rows).
2. **ORDER BY descending**: Si quieres ultimas N, usa DESC en ORDER.
3. **ROWS vs RANGE**: `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` = toda la partition.
4. **Evitar subconsultas**: Window functions NO requieren subqueries si usas CTEs.

```sql
-- LENTO: 2 scans de tabla
SELECT *
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY created_at) AS rn
  FROM tracking_events
) sub
WHERE rn <= 5;

-- RAPIDO: 1 scan, solo output
WITH ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY created_at) AS rn
  FROM tracking_events
)
SELECT * FROM ranked WHERE rn <= 5;
```

---

## Referencias

- [PostgreSQL Window Functions](https://www.postgresql.org/docs/current/functions-window.html)
- [LAG and LEAD (Neon Docs)](https://neon.com/docs/functions/window-lag)
- [Data Processing With PostgreSQL Window Functions (TigerData)](https://www.tigerdata.com/learn/postgresql-window-functions)
