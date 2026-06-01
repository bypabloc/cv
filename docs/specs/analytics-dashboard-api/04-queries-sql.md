# 04 — Queries SQL por endpoint

[< 03-infraestructura](03-infraestructura.md) | [Siguiente: 05-cache-layer >](05-cache-layer.md)

> SQL plano por endpoint (no SQLAlchemy expression-style aqui — para
> que sea legible y se pueda probar en `psql`). En el codigo, los
> services usan `select(...).where(...)` con SQLAlchemy 2.x, pero la
> semantica es la misma.

## 0. Convenciones

- `:date_from`, `:date_to`: parametros bindeados (psycopg quote-safe).
- Particion: `vis_tracking_events` esta particionada por `created_at`
  (mensual). Toda query DEBE incluir `created_at >= :date_from AND
  created_at < :date_to` para podarPartitions.
- `WHERE` por rango fechas usa `>= from AND < to + INTERVAL '1 day'`
  (half-open) para alinear con la convencion ISO.
- `LIMIT` siempre explicito.

## 1. `analytics/overview`

7 KPIs en una sola transaccion. Cada subquery es 1 round-trip a Neon.

```sql
-- sessions: visitantes unicos por first_seen_at en rango
SELECT count(*) FROM vis_sessions
WHERE first_seen_at >= :date_from AND first_seen_at < :date_to;

-- visits: sesiones-visita (multiples por session)
SELECT count(*) FROM vis_session_visits
WHERE started_at >= :date_from AND started_at < :date_to;

-- events: eventos totales
SELECT count(*) FROM vis_tracking_events
WHERE created_at >= :date_from AND created_at < :date_to;

-- contacts: contactos recibidos
SELECT count(*) FROM vis_contacts
WHERE created_at >= :date_from AND created_at < :date_to;

-- unique_visitors: sessions distintas con al menos 1 visit en el rango
SELECT count(DISTINCT session_id) FROM vis_session_visits
WHERE started_at >= :date_from AND started_at < :date_to;

-- avg_visit_duration_sec: media de (ended_at - started_at) en segundos
SELECT COALESCE(AVG(EXTRACT(epoch FROM (ended_at - started_at))), 0)
FROM vis_session_visits
WHERE ended_at IS NOT NULL
  AND started_at >= :date_from AND started_at < :date_to;

-- bounce_rate: visits con event_count == 1 / total visits
SELECT count(*) FROM vis_session_visits
WHERE event_count = 1
  AND started_at >= :date_from AND started_at < :date_to;
```

**Optimizacion**: si las 7 queries en serie son > 500 ms, consolidar
con UNION ALL + subqueries inline. Actual estimate: 7 * ~30 ms = ~200 ms.
Aceptable.

**Indices necesarios** (verificar que existan; si no, migration nueva):

```sql
CREATE INDEX IF NOT EXISTS idx_vis_sessions_first_seen_at
  ON vis_sessions (first_seen_at);
CREATE INDEX IF NOT EXISTS idx_vis_session_visits_started_at
  ON vis_session_visits (started_at);
CREATE INDEX IF NOT EXISTS idx_vis_contacts_created_at
  ON vis_contacts (created_at);
-- vis_tracking_events.created_at YA es partition key, no necesita indice extra.
```

## 2. `analytics/timeseries`

```sql
-- bucket=day | hour | week
SELECT
  date_trunc(:bucket, created_at) AS ts,
  count(*) AS count
FROM vis_tracking_events
WHERE created_at >= :date_from AND created_at < :date_to
  AND (:niche IS NULL OR niche = :niche)
  AND (:event_type IS NULL OR event_type_id = (
       SELECT id FROM tax_event_types WHERE code_name = :event_type
     ))
GROUP BY ts
ORDER BY ts ASC
LIMIT 8784;  -- max 1 year hourly
```

**Output shape**: `{bucket, points: [{timestamp, count}], from, to,
filters: {niche, event_type}}`.

## 3. `analytics/top-pages`

```sql
SELECT
  page_path,
  count(*) AS events,
  count(DISTINCT session_id) AS unique_visitors,
  count(DISTINCT visit_id) AS unique_visits
FROM vis_tracking_events
WHERE created_at >= :date_from AND created_at < :date_to
  AND page_path IS NOT NULL
  AND (:niche IS NULL OR niche = :niche)
GROUP BY page_path
ORDER BY events DESC
LIMIT :limit;  -- default 10, max 50
```

**Output**: `{items: [{page_path, events, unique_visitors, unique_visits}]}`.

## 4. `analytics/top-referrers`

```sql
SELECT
  COALESCE(referrer, '(direct)') AS referrer,
  count(*) AS visits,
  count(DISTINCT session_id) AS unique_visitors
FROM vis_session_visits
WHERE started_at >= :date_from AND started_at < :date_to
GROUP BY referrer
ORDER BY visits DESC
LIMIT :limit;
```

Variante adicional: rankings de UTM source/medium/campaign. Se devuelven
en el mismo response bajo 4 listas:

```sql
-- UTM source
SELECT utm_source, count(*) AS visits
FROM vis_session_visits
WHERE started_at >= :date_from AND started_at < :date_to
  AND utm_source IS NOT NULL
GROUP BY utm_source
ORDER BY visits DESC LIMIT 20;

-- idem medium / campaign / content / term
```

**Output**: `{referrers: [...], utm_sources: [...], utm_mediums: [...],
utm_campaigns: [...]}`.

## 5. `analytics/top-niches`

```sql
SELECT
  COALESCE(niche, '(none)') AS niche,
  count(*) AS visits,
  count(DISTINCT session_id) AS unique_visitors
FROM vis_session_visits
WHERE started_at >= :date_from AND started_at < :date_to
GROUP BY niche
ORDER BY visits DESC
LIMIT :limit;
```

## 6. `analytics/active-now`

Cache TTL corto (10s) para que sea casi en tiempo real.

```sql
SELECT count(*) AS active_sessions
FROM vis_sessions
WHERE last_seen_at >= NOW() - INTERVAL '5 minutes';
```

**Output**: `{active_sessions, threshold_minutes: 5, as_of: <iso8601>}`.

## 7. `analytics/retention`

```sql
-- new vs returning visitors en el rango
WITH visits_in_range AS (
  SELECT DISTINCT session_id
  FROM vis_session_visits
  WHERE started_at >= :date_from AND started_at < :date_to
)
SELECT
  count(*) FILTER (WHERE s.first_seen_at >= :date_from AND s.first_seen_at < :date_to) AS new_visitors,
  count(*) FILTER (WHERE s.first_seen_at < :date_from) AS returning_visitors,
  count(*) AS total
FROM visits_in_range v
JOIN vis_sessions s ON s.session_id = v.session_id;
```

**Output**: `{new_visitors, returning_visitors, total, returning_rate}`.

## 8. `events/distribution`

```sql
SELECT
  COALESCE(t.code_name, '(unknown)') AS event_type,
  count(*) AS count,
  ROUND(100.0 * count(*) / SUM(count(*)) OVER (), 2) AS pct
FROM vis_tracking_events e
LEFT JOIN tax_event_types t ON t.id = e.event_type_id
WHERE e.created_at >= :date_from AND e.created_at < :date_to
GROUP BY t.code_name
ORDER BY count DESC;
```

**Output**: `{items: [{event_type, count, pct}]}`.

## 9. `events/list`

Listado paginado. Filtros opcionales: `niche`, `event_type`, `session_id`,
`page_path`.

```sql
SELECT
  e.created_at,
  e.visit_id,
  e.page_id,
  e.session_id,
  e.page_path,
  e.niche,
  e.viewport_width,
  e.viewport_height,
  t.code_name AS event_type,
  e.event_props
FROM vis_tracking_events e
LEFT JOIN tax_event_types t ON t.id = e.event_type_id
WHERE e.created_at >= :date_from AND e.created_at < :date_to
  AND (:niche IS NULL OR e.niche = :niche)
  AND (:event_type IS NULL OR t.code_name = :event_type)
  AND (:session_id IS NULL OR e.session_id = :session_id)
  AND (:page_path IS NULL OR e.page_path = :page_path)
ORDER BY e.created_at DESC
LIMIT :page_size OFFSET :offset;

-- count para `total`
SELECT count(*) FROM vis_tracking_events e
LEFT JOIN tax_event_types t ON t.id = e.event_type_id
WHERE e.created_at >= :date_from AND e.created_at < :date_to
  AND (:niche IS NULL OR e.niche = :niche)
  AND (:event_type IS NULL OR t.code_name = :event_type)
  AND (:session_id IS NULL OR e.session_id = :session_id)
  AND (:page_path IS NULL OR e.page_path = :page_path);
```

**Output**: `{items: [...], page, page_size, total, has_more}`.

> El count() en un listado paginado es costoso. Si el `total` resulta
> lento (>500ms con 1M+ filas), cambiar a `has_more` calculado pidiendo
> `LIMIT (page_size + 1)` y descartar el extra. Por ahora, `total`
> exacto es aceptable (volumen actual ~15k events/mes).

## 10. `events/heatmap`

Dia de la semana (0=lunes ISO) x hora (0-23).

```sql
SELECT
  EXTRACT(isodow FROM created_at)::int AS dow,
  EXTRACT(hour FROM created_at)::int  AS hour,
  count(*) AS count
FROM vis_tracking_events
WHERE created_at >= :date_from AND created_at < :date_to
GROUP BY dow, hour
ORDER BY dow, hour;
```

**Output**: `{cells: [{dow, hour, count}]}` (max 7*24=168 celdas).

## 11. `sessions/list`

```sql
SELECT
  s.session_id,
  s.first_seen_at,
  s.last_seen_at,
  s.browser,
  s.browser_version,
  s.os,
  s.device_type,
  count(v.visit_id) AS visits_count
FROM vis_sessions s
LEFT JOIN vis_session_visits v ON v.session_id = s.session_id
  AND v.started_at >= :date_from AND v.started_at < :date_to
WHERE s.first_seen_at >= :date_from AND s.first_seen_at < :date_to
  AND (:device_type IS NULL OR s.device_type = :device_type)
  AND (:browser IS NULL OR s.browser = :browser)
GROUP BY s.session_id
ORDER BY s.last_seen_at DESC
LIMIT :page_size OFFSET :offset;
```

## 12. `sessions/detail`

3 queries:

```sql
-- 1. La sesion (columnas explicitas para no filtrar PII no intencionada
--    y evitar romper el Pydantic model si el schema agrega columnas)
SELECT
  session_id,
  first_seen_at,
  last_seen_at,
  browser,
  browser_version,
  os,
  device_type
FROM vis_sessions
WHERE session_id = :session_id;

-- 2. Sus visits (todas, ordenadas)
SELECT visit_id, started_at, ended_at, event_count, ip, country,
       utm_source, utm_medium, utm_campaign, referrer,
       landing_page_path, niche
FROM vis_session_visits
WHERE session_id = :session_id
ORDER BY started_at ASC;

-- 3. Count de eventos
SELECT count(*) FROM vis_tracking_events
WHERE session_id = :session_id;
```

**Output**: `{session, visits: [...], events_count}` o
`{is_valid: false, code: 4040, data: null}` si no existe.

## 13. `visits/list`

```sql
SELECT
  v.visit_id,
  v.session_id,
  v.started_at,
  v.ended_at,
  v.event_count,
  v.ip,
  v.country,
  v.utm_source, v.utm_medium, v.utm_campaign,
  v.referrer,
  v.landing_page_path,
  v.niche
FROM vis_session_visits v
WHERE v.started_at >= :date_from AND v.started_at < :date_to
  AND (:niche IS NULL OR v.niche = :niche)
  AND (:country IS NULL OR v.country = :country)
ORDER BY v.started_at DESC
LIMIT :page_size OFFSET :offset;
```

## 14. `visits/landing-pages`

```sql
SELECT
  landing_page_path,
  count(*) AS visits,
  count(DISTINCT session_id) AS unique_visitors
FROM vis_session_visits
WHERE started_at >= :date_from AND started_at < :date_to
  AND landing_page_path IS NOT NULL
GROUP BY landing_page_path
ORDER BY visits DESC
LIMIT :limit;
```

## 15. `geo/by-country`

```sql
WITH session_data AS (
  SELECT
    COALESCE(country, 'XX') AS country,
    session_id
  FROM vis_session_visits
  WHERE started_at >= :date_from AND started_at < :date_to
),
country_sessions_visits AS (
  SELECT
    country,
    count(DISTINCT session_id) AS sessions,
    count(*) AS visits
  FROM session_data
  GROUP BY country
),
country_events AS (
  SELECT
    sd.country,
    count(*) AS events
  FROM session_data sd
  JOIN vis_tracking_events e
    ON e.session_id = sd.session_id
   AND e.occurred_at >= :date_from
   AND e.occurred_at < :date_to
  GROUP BY sd.country
)
SELECT
  csv.country,
  csv.sessions,
  csv.visits,
  COALESCE(ce.events, 0) AS events
FROM country_sessions_visits csv
LEFT JOIN country_events ce USING (country)
ORDER BY csv.sessions DESC
LIMIT :limit;
```

El CTE `session_data` materializa las sesiones del rango con su country.
`country_sessions_visits` cuenta sesiones y visits (PV) por pais.
`country_events` hace `JOIN` (no `LEFT JOIN`) sobre `vis_tracking_events`
limitado al mismo rango — paises sin eventos en el rango no aparecen aqui.
El `LEFT JOIN ... USING (country)` final preserva paises con sesiones pero
0 eventos: el `COALESCE(ce.events, 0)` garantiza `events: 0` (no NULL) en
el response, cumpliendo el shape de AC-13 `{country, sessions, visits, events}`.

## 16. `devices/breakdown`

3 distribuciones en un solo response:

```sql
-- device_types
SELECT COALESCE(device_type, '(unknown)') AS device_type,
       count(*) AS sessions
FROM vis_sessions
WHERE first_seen_at >= :date_from AND first_seen_at < :date_to
GROUP BY device_type ORDER BY sessions DESC;

-- browsers
SELECT COALESCE(browser, '(unknown)') AS browser,
       count(*) AS sessions
FROM vis_sessions
WHERE first_seen_at >= :date_from AND first_seen_at < :date_to
GROUP BY browser ORDER BY sessions DESC LIMIT 20;

-- os
SELECT COALESCE(os, '(unknown)') AS os,
       count(*) AS sessions
FROM vis_sessions
WHERE first_seen_at >= :date_from AND first_seen_at < :date_to
GROUP BY os ORDER BY sessions DESC LIMIT 20;
```

**Output**: `{device_types: [...], browsers: [...], os: [...]}`.

## 17. `funnel/conversion`

```sql
WITH s AS (SELECT count(*) AS n FROM vis_sessions
           WHERE first_seen_at >= :date_from AND first_seen_at < :date_to),
     v AS (SELECT count(DISTINCT session_id) AS n FROM vis_session_visits
           WHERE started_at >= :date_from AND started_at < :date_to),
     c AS (SELECT count(*) AS n FROM vis_contacts
           WHERE created_at >= :date_from AND created_at < :date_to)
SELECT s.n AS sessions, v.n AS visits, c.n AS contacts
FROM s, v, c;
```

**Output**:

```json
{
  "sessions": 1234,
  "visits": 980,
  "contacts": 42,
  "session_to_visit_rate": 0.794,
  "visit_to_contact_rate": 0.043,
  "session_to_contact_rate": 0.034
}
```

Rates calculados en Python (no en SQL) para manejar division por cero.

## 18. `contacts/list`

```sql
SELECT
  id, created_at, name, email, message, company, role,
  service_type, budget, timeline, niche, status, session_id
FROM vis_contacts
WHERE created_at >= :date_from AND created_at < :date_to
  AND (:status IS NULL OR status = :status)
  AND (:niche IS NULL OR niche = :niche)
ORDER BY created_at DESC
LIMIT :page_size OFFSET :offset;
```

## 19. `contacts/by-status`

```sql
SELECT
  status,
  count(*) AS count,
  ROUND(100.0 * count(*) / SUM(count(*)) OVER (), 2) AS pct
FROM vis_contacts
WHERE created_at >= :date_from AND created_at < :date_to
GROUP BY status
ORDER BY count DESC;
```

## 20. Resumen de indices necesarios

Antes de mergear, verificar que existan estos indices en Neon. Si
alguno falta, agregar una migration Alembic separada (no parte de este
plan, pero **prerequisito**):

```sql
-- vis_sessions
CREATE INDEX IF NOT EXISTS idx_vis_sessions_first_seen_at ON vis_sessions (first_seen_at);
CREATE INDEX IF NOT EXISTS idx_vis_sessions_last_seen_at  ON vis_sessions (last_seen_at);
CREATE INDEX IF NOT EXISTS idx_vis_sessions_device_type   ON vis_sessions (device_type);
CREATE INDEX IF NOT EXISTS idx_vis_sessions_browser       ON vis_sessions (browser);

-- vis_session_visits
CREATE INDEX IF NOT EXISTS idx_vsv_started_at ON vis_session_visits (started_at);
CREATE INDEX IF NOT EXISTS idx_vsv_session_id ON vis_session_visits (session_id);
CREATE INDEX IF NOT EXISTS idx_vsv_country    ON vis_session_visits (country);
CREATE INDEX IF NOT EXISTS idx_vsv_niche      ON vis_session_visits (niche);
CREATE INDEX IF NOT EXISTS idx_vsv_referrer   ON vis_session_visits (referrer);

-- vis_tracking_events (la tabla esta particionada por created_at; los indices son local a particion)
CREATE INDEX IF NOT EXISTS idx_vte_session_id  ON vis_tracking_events (session_id);
CREATE INDEX IF NOT EXISTS idx_vte_event_type  ON vis_tracking_events (event_type_id);
CREATE INDEX IF NOT EXISTS idx_vte_page_path   ON vis_tracking_events (page_path);
CREATE INDEX IF NOT EXISTS idx_vte_niche       ON vis_tracking_events (niche);

-- vis_contacts
CREATE INDEX IF NOT EXISTS idx_vc_created_at  ON vis_contacts (created_at);
CREATE INDEX IF NOT EXISTS idx_vc_status      ON vis_contacts (status);
CREATE INDEX IF NOT EXISTS idx_vc_niche       ON vis_contacts (niche);
```

Comando para verificar en dev:

```bash
DB_URL="$(grep -m1 '^DB_URL=' docker/env/server/.dev | cut -d= -f2-)" \
  psql "$DB_URL" -c "\\d+ vis_sessions" | grep Indexes -A 20
```

Si falta alguno, agregar como **fase 0.5** (Alembic migration nueva
ANTES de empezar a deployar el Lambda).

[< 03-infraestructura](03-infraestructura.md) | [Siguiente: 05-cache-layer >](05-cache-layer.md)
