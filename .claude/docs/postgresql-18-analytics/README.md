# PostgreSQL 18 para analytics del portfolio

> Conocimiento consolidado sobre como usar PostgreSQL 18 (Neon) para analytics del portfolio: contactos normalizados, tracking events con range partitioning, agregaciones diarias, y queries de analytics con window functions.

**Verificado**: 2026-05-14
**Stack**: Astro 6 + Lambda Python 3.13 + PostgreSQL 18 (Neon)

## Cuando leer cada archivo

| Tema | Archivo | Cuando leer |
|------|---------|-------------|
| Features clave de PG18 para analytics | [01-pg18-features-for-analytics.md](./01-pg18-features-for-analytics.md) | Entender AIO, virtual generated columns, UUIDv7, skip scan, RETURNING OLD/NEW |
| Diseno SQL de 4 esquemas del proyecto | [02-schema-design-this-project.md](./02-schema-design-this-project.md) | Crear tablas: `contacts`, `tracking_events`, `tracking_daily_aggregates`, `daily_metrics` |
| Estrategia de indexes (B-tree, GIN, BRIN, GiST) | [03-indexes-strategy.md](./03-indexes-strategy.md) | Elegir tipo de index y escaneamento para cada tabla y query |
| Window functions para analytics | [04-window-functions-analytics.md](./04-window-functions-analytics.md) | Queries con LAG/LEAD, ROW_NUMBER, session journey reconstruction |
| Materialized views y refresh scheduling | [05-materialized-views.md](./05-materialized-views.md) | Crear vistas materializadas, refreshearlas con pg_cron, REFRESH CONCURRENTLY |
| Range partitioning de tracking_events | [06-partitioning-tracking.md](./06-partitioning-tracking.md) | Particionar por mes, drop partition para retention 60d en < 1ms |
| JSONB para campos flexibles | [07-jsonb-flexible-fields.md](./07-jsonb-flexible-fields.md) | Cuando usar JSONB, operadores, GIN indexes, anti-patterns |
| 10 queries listas para dashboard | [08-queries-dashboard.md](./08-queries-dashboard.md) | Copy-paste queries: conversions, attribution, bounce rate, heat map, etc. |
| PG18 vs alternativas (ClickHouse, BigQuery, TimescaleDB) | [09-pg18-vs-alternatives.md](./09-pg18-vs-alternatives.md) | Por que PG18 para este volumen, cuando considerar upgrade |
| Gotchas y troubleshooting | [10-gotchas.md](./10-gotchas.md) | Errores comunes, timezone issues, query performance debugging |

## Reglas criticas

- SIEMPRE usar UUIDv7 como PK en todas las tablas (generado al insertar, no después)
- SIEMPRE crear indexes ANTES de las inserciones masivas (Lambda) para evitar query overhead
- SIEMPRE particionar `tracking_events` por mes; drop partitions > 60d via pg_cron ANTES de que crezcan
- NUNCA consultar toda la tabla `tracking_events` sin WHERE clause en fecha — siempre aplica range de dias
- SIEMPRE usar JSONB para campos que no quieres tipar al inicio (audit metadata, A/B test variants)
- NUNCA hacer SELECT * en queries de analytics — especificar columnas exactas
- SIEMPRE REFRESH MATERIALIZED VIEW CONCURRENTLY para no bloquear lectores
- SIEMPRE validar que GIN indexes existen antes de hacer full-text search en `contacts.message`

## Quick start: crear schema

```bash
# 1. Conectar a Neon (reemplaza con tu cadena de conexion)
psql postgresql://user:password@ep-xxx.neon.tech/portfolio

# 2. Crear tablas (ver 02-schema-design-this-project.md)
CREATE TABLE contacts (id UUID PRIMARY KEY DEFAULT uuidv7(), ...);
CREATE TABLE tracking_events (id UUID PRIMARY KEY DEFAULT uuidv7(), ...)
  PARTITION BY RANGE (created_at);
CREATE TABLE tracking_daily_aggregates (...);
CREATE TABLE daily_metrics (...);

# 3. Crear indexes (ver 03-indexes-strategy.md)
CREATE INDEX idx_tracking_events_created_at ON tracking_events(created_at);
CREATE INDEX idx_contacts_message_fts ON contacts USING GIN (
  to_tsvector('spanish', message)
);

# 4. Crear materialized views (ver 05-materialized-views.md)
CREATE MATERIALIZED VIEW mv_contacts_by_month_niche AS ...;

# 5. Programar refreshes (pg_cron en Neon)
SELECT cron.schedule('refresh_mv_daily', '0 1 * * *', 
  'REFRESH MATERIALIZED VIEW CONCURRENTLY mv_contacts_by_month_niche');

# 6. Test queries (ver 08-queries-dashboard.md)
SELECT * FROM contacts_by_month_niche LIMIT 10;
```

## Estado actual del arquitectura

- **Fuente de datos**: Lambda form + Lambda tracking -> DynamoDB
- **DynamoDB Streams**: Gatilla Lambda processor
- **Lambda processor**: Lee DynamoDB -> INSERT en PostgreSQL 18 (Neon)
- **PostgreSQL 18 Neon**: 4 esquemas, range partitioned, materialized views
- **Queries**: CTEs + window functions, refresh diario via pg_cron
- **Retention**: Drop partitions > 60d automaticamente
- **Volumen esperado**: ~200 contacts/mes, ~15k tracking events/mes (< 2MB diarios)

## Referencias relacionadas

- `.claude/docs/postgresql-18/` — Referencia tecnica de PG18 (features del motor, config)
- `.claude/rules/neon-management.md` — Gestion operativa de Neon (migrations, branches, SSM)
- `.claude/rules/python.md` — Code style para devtools que orquesten PG (psycopg3, type hints)

## Tabla de contenidos

1. [Features PG18](./01-pg18-features-for-analytics.md) — AIO, UUIDv7, virtual cols, skip scan
2. [Schema design](./02-schema-design-this-project.md) — 4 tablas, ER diagram, CREATE TABLE
3. [Indexes](./03-indexes-strategy.md) — B-tree, GIN, BRIN, GiST strategies
4. [Window functions](./04-window-functions-analytics.md) — LAG/LEAD, ROW_NUMBER, session reconstruction
5. [Materialized views](./05-materialized-views.md) — REFRESH CONCURRENTLY, pg_cron scheduling
6. [Partitioning](./06-partitioning-tracking.md) — Range by month, auto-cleanup
7. [JSONB fields](./07-jsonb-flexible-fields.md) — GIN indexes, when to use
8. [Dashboard queries](./08-queries-dashboard.md) — 10 ready-to-use analytics queries
9. [PG18 vs alternatives](./09-pg18-vs-alternatives.md) — ClickHouse, BigQuery, TimescaleDB
10. [Gotchas](./10-gotchas.md) — Common issues, debugging, timezone
