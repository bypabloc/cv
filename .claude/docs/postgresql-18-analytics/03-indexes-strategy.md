# Estrategia de indexes

> Que tipo de index usar en cada columna y query. B-tree, GIN, BRIN, GiST tienen tradeoffs distintos.

**Verificado**: 2026-05-14

[← Schema design](./02-schema-design-this-project.md) | [README](./README.md) | [Siguiente: Window functions →](./04-window-functions-analytics.md)

## Decision matrix: tipo de index

| Tipo | Mejor para | Worst case | Insert overhead | Size |
|------|-----------|-----------|-----------------|------|
| **B-tree** | Escalares (INT, TEXT, DATE), range queries | NOTHING | Bajo-medio | ~3MB |
| **GIN** | JSONB, arrays, full-text search | UPDATE-heavy | Alto | ~5MB |
| **BRIN** | Columnas ordenadas por tiempo, tabla > 10M rows | Random inserts | Muy bajo | ~1MB |
| **GiST** | Espacial (geo), full-text | Random data | Medio | ~2MB |
| **Hash** | Igualdad (`=`) | Range queries (`<`, `>`) | Muy bajo | ~2MB |

## Tabla `contacts` - indexes

### PK + UNIQUE
```sql
-- Ya esta: id UUID PRIMARY KEY (B-tree automatico)
-- Ya esta: email VARCHAR UNIQUE (B-tree automatico)
```

### Indexes secundarios (OLTP - escritura baja)

```sql
-- Para queries: "contactos del mes pasado"
CREATE INDEX idx_contacts_created_at ON contacts(created_at DESC);

-- Para queries: "contactos por niche"
CREATE INDEX idx_contacts_niche ON contacts(niche);

-- Para queries: "contactos por tipo de servicio"
CREATE INDEX idx_contacts_service_type ON contacts(service_type);

-- Para queries: "buscar contactos que mencionan 'python'"
-- IMPORTANTE: GIN con full-text search en espanol
CREATE INDEX idx_contacts_message_fts ON contacts USING GIN (
  to_tsvector('spanish', message)
);

-- Para queries: "contactos device mobile con utm_source email"
-- Nota: metadata es JSONB, GIN con jsonb_path_ops (mejor perf que jsonb_ops)
CREATE INDEX idx_contacts_metadata ON contacts USING GIN (
  metadata jsonb_path_ops
);

-- Opcional: multicolumna si quieres (niche + service_type)
CREATE INDEX idx_contacts_niche_service ON contacts(niche, service_type);
```

**Total**: ~6 indexes, ~10MB en disk.

## Tabla `tracking_events` - indexes (CRITICAL)

Esta tabla crece rapido (~500 filas/dia). Indexes son CRITICOS para queries de analytics.

### Por partition (hereda del parent)

```sql
-- Timestamp descending (para "ultimas N paginas vistas")
CREATE INDEX idx_tracking_events_created_at ON tracking_events(created_at DESC);

-- Session tracking (para "session journey de un usuario")
CREATE INDEX idx_tracking_events_session_id ON tracking_events(session_id);

-- Page analytics (para "top 10 paginas")
CREATE INDEX idx_tracking_events_page_path ON tracking_events(page_path);

-- UTM attribution (para "conversions por campana")
CREATE INDEX idx_tracking_events_utm_source ON tracking_events(utm_source);

-- MULTICOLUMNA para queries tipo "paginas vistas en septiembre"
-- Skip scan en PG18 hace esto eficiente incluso sin leading column
CREATE INDEX idx_tracking_events_date_page ON tracking_events(
  date_trunc('day', created_at),
  page_path,
  utm_source
);

-- JSONB para device/browser/country
CREATE INDEX idx_tracking_events_extra ON tracking_events USING GIN (
  extra jsonb_path_ops
);

-- BRIN para tabla particionada (alternativa a B-tree si tabla crecia sin limite)
-- Hoy NO usar BRIN, pero es buena alternativa si datos crece 100x
-- CREATE INDEX idx_tracking_events_created_at_brin ON tracking_events USING BRIN (created_at);
```

**Construccion**: Usar `CONCURRENTLY` para no bloquear inserciones.
```sql
-- Durante horario no-peak
CREATE INDEX CONCURRENTLY idx_tracking_events_created_at 
ON tracking_events(created_at DESC);
```

**Total**: ~6 indexes, ~25MB en disk (crece con particiones).

## Tabla `tracking_daily_aggregates` - indexes

```sql
-- Para queries: "ultimas 7 dias"
CREATE INDEX idx_daily_agg_date ON tracking_daily_aggregates(date DESC);

-- Para queries: "top paginas en un periodo"
CREATE INDEX idx_daily_agg_page ON tracking_daily_aggregates(page_path);

-- Para queries: "conversions por campana"
CREATE INDEX idx_daily_agg_utm ON tracking_daily_aggregates(utm_source);

-- Multicolumna (PK) es suficiente para queries (date, page, utm)
```

**Total**: ~3 indexes, ~5MB en disk.

## Tabla `daily_metrics` - indexes

```sql
-- Solo una query: select * where date > X
CREATE INDEX idx_daily_metrics_date ON daily_metrics(date DESC);

-- El resto son JSONB columns que rara vez se queryean (estan embebidos)
```

**Total**: ~1 index, ~1MB en disk.

---

## Anti-patterns (EVITAR)

### 1. Index en TODA columna (antes de profiling)

MAL:
```sql
-- No hagas esto sin probar la query primero
CREATE INDEX idx_contacts_first_name ON contacts(first_name);
CREATE INDEX idx_contacts_last_name ON contacts(last_name);
CREATE INDEX idx_contacts_message ON contacts(message);  -- Huge!
```

BIEN: Mide primero:
```sql
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM contacts WHERE first_name = 'Pablo';
-- Si cost > 1000, entonces agrega index
```

### 2. Multicolumna sin entender order

MAL:
```sql
-- Orden erroneo: no hay queries WHERE first_name AND last_name
CREATE INDEX idx_contacts_name ON contacts(first_name, last_name);
```

BIEN:
```sql
-- Orden correcto: queries actuales usan este
CREATE INDEX idx_contacts_created_at_niche ON contacts(created_at DESC, niche);
```

### 3. GIN en columna con UPDATE frecuentes

MAL:
```sql
-- metadata se actualiza constantemente, GIN index es caro
CREATE INDEX idx_contacts_metadata ON contacts USING GIN (metadata);
```

MEJOR: Deja sin index, o usa BRIN si tabla es enorme y metadata casi nunca se modifica.

### 4. Olvidar `CONCURRENTLY` en tablas live

MAL:
```sql
-- Bloquea todas las inserciones mientras se construye
CREATE INDEX idx_tracking_events_session ON tracking_events(session_id);
```

BIEN:
```sql
-- No bloquea
CREATE INDEX CONCURRENTLY idx_tracking_events_session ON tracking_events(session_id);
```

---

## Index Maintenance (monitoring)

### Ver tamano de cada index
```sql
SELECT
  schemaname,
  tablename,
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Ver indexes unused (candidatos a DROP)
```sql
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexname NOT LIKE 'pg_toast%'
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Rebuild index (si fragmentation > 30%)
```sql
-- Sin bloquear
REINDEX INDEX CONCURRENTLY idx_tracking_events_created_at;

-- O recrear desde cero
DROP INDEX CONCURRENTLY idx_tracking_events_created_at;
CREATE INDEX CONCURRENTLY idx_tracking_events_created_at 
ON tracking_events(created_at DESC);
```

---

## Recomendaciones finales

| Tabla | Index strategy | Esperado |
|-------|---|---|
| `contacts` (200 filas) | 6 indexes: PK + UNIQUE + niche + service_type + FTS + JSONB | OLTP ok |
| `tracking_events` (500 filas/dia) | 6 indexes: created_at + session + page + utm + multicolumna + JSONB | OLAP optimizado |
| `tracking_daily_aggregates` (~90 filas) | 3 indexes: date + page + utm | Simple |
| `daily_metrics` (~365 filas) | 1 index: date | Minimal |

---

## Referencias

- [PostgreSQL B-tree Index](https://www.postgresql.org/docs/current/sql-createindex.html)
- [PostgreSQL GIN Indexes](https://www.postgresql.org/docs/current/gin.html)
- [PostgreSQL Index Types](https://www.postgresql.org/docs/current/indexes-types.html)
- [Mastering PostgreSQL GIN Indexes (Medium)](https://medium.com/@vedantthakkar1003/mastering-postgresql-gin-indexes-the-ultimate-guide-to-faster-jsonb-array-and-full-text-search-f1f8ec3e67af)
