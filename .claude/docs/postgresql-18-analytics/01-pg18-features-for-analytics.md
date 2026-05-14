# PG18 Features para analytics

> Que features de PostgreSQL 18 (lanzado Sept 2025) son relevantes para tu caso: analytics de contactos + tracking events con alto volumen de inserciones.

**Verificado**: 2026-05-14 | **Fuente**: postgresql.org release notes

[← README](./README.md) | [Siguiente: Schema design →](./02-schema-design-this-project.md)

## Asynchronous I/O (AIO)

PostgreSQL 18 introduce un subsistema de I/O asincronico que mejora:
- Escaneos secuenciales (table scans)
- Bitmap heap scans
- Operaciones VACUUM
- Sequential writes (ej. WAL)

**Beneficio**: 3x mejora en throughput de lectura en SSD/almacenamiento rapido.

**En tu proyecto**: Cuando Lambda processor hace batch INSERT de 1000s de tracking events, la escritura es secuencial. AIO la paraleliza automaticamente.

**Control**:
```sql
-- Ver si AIO esta activo
SHOW io_method;  -- debe ser 'io_uring' en Linux 5.1+, fallback a 'posix'

-- Ver stats de I/O asincronico
SELECT * FROM pg_stat_io;  -- Nueva tabla en PG18
```

## Virtual Generated Columns (default)

Columnas que computan su valor **al leer**, no al insertar.

**Ejemplo**:
```sql
CREATE TABLE contacts (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  message TEXT,
  message_length INT GENERATED ALWAYS AS (length(message)) VIRTUAL
);

-- Al SELECT, message_length se calcula on-the-fly
-- No ocupa storage, no ralentiza INSERT
SELECT id, message, message_length FROM contacts;
```

**En tu proyecto**: Usa para derivados sin storage (ej. `full_name` = CONCAT(first_name, last_name)).

## Skip Scan en B-tree Indexes

En PG18, indexes multicolumna (B-tree) pueden usarse incluso si NO hay restriccion en las primeras columnas.

**Ejemplo**: Index en `(created_at, page_id)`.
```sql
-- Vieja forma: sin index en esta query
SELECT * FROM tracking_events
WHERE page_id = '/portfolio'  -- sin created_at = X
ORDER BY created_at DESC;

-- PG18: usa el index, hace "skip scan"
-- Busca todas las hojas, salta rapido entre valores diferentes de created_at
EXPLAIN ANALYZE SELECT * FROM tracking_events
WHERE page_id = '/portfolio'
ORDER BY created_at DESC;
```

**Beneficio**: 5-10x mas rapido comparado a sequential scan.

## UUIDv7 (timestamp-ordered)

Función nativa `uuidv7()` genera UUIDs ordenables por tiempo.

**Ventaja sobre UUIDv4**:
- UUIDv4 es random → inserciones en B-tree son caóticas (page splits frecuentes)
- UUIDv7 = timestamp (48 bits) + random (78 bits) → ordenables, ✅ para clustered PKs
- Mejor locality, menos page fragmentation, ~10% menos WAL

**Sintaxis**:
```sql
CREATE TABLE tracking_events (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**En tu proyecto**: PK en todas las tablas. Lambda processor simplemente `DEFAULT uuidv7()`.

## RETURNING OLD / NEW (todas las operaciones)

INSERT, UPDATE, DELETE, MERGE ahora pueden usar `RETURNING OLD.*` y `RETURNING NEW.*`.

**Caso de uso**: audit logging + bi-directional sync.

```sql
-- Antes: necesitabas 2 queries
DELETE FROM contacts WHERE id = $1 RETURNING *;
INSERT INTO contacts_archive VALUES (...);

-- Ahora:
DELETE FROM contacts WHERE id = $1
RETURNING OLD.* AS deleted_record;

-- O INSERT:
INSERT INTO contacts (email, message) VALUES ($1, $2)
RETURNING NEW.id, NEW.created_at;
```

**En tu proyecto**: Lambda processor puede hacer `INSERT ... RETURNING id` para confirmar al cliente.

## Skip Scan + BRINIndexes (combinado)

BRIN = Block Range Index. Optimizado para tablas ENORMES ordenadas por tiempo.

**Para tracking_events con 15k eventos/mes**:
- Al año: 180k rows
- Al quinto año: 900k rows (aun pequeño)

Aun asi, BRIN es mucho mas chico que B-tree:
```sql
-- B-tree multicolumna: ~50MB
CREATE INDEX idx_tracking_btree ON tracking_events(created_at, page_id);

-- BRIN: ~1MB (por lo que la tabla esta ordenada por created_at)
CREATE INDEX idx_tracking_brin ON tracking_events USING BRIN (created_at);
```

**Decision para ti**: Usa BRIN solo si tabla crece >10M rows. Hoy quedate con B-tree + skip scan.

## Mejoras en Vacuum

- Normal VACUUM ahora puede **congelar paginas** (freeze) inline
- Reduce overhead de freezing completo posterior
- Variable `vacuum_max_eager_freeze_failure_rate` controla agresividad

**Impacto**: Menos "vacuum storms" en carga alta. Para portfolio, cambio minimo.

## Parallel GIN Index Creation

`CREATE INDEX` en GIN puede paralelizar (aprox. N_WORKERS).

**Ejemplo**:
```sql
-- Aprox 4x mas rapido si `max_parallel_workers` >= 2
CREATE INDEX idx_contacts_message_fts ON contacts USING GIN (
  to_tsvector('spanish', message)
) WITH (fillfactor=70);

-- Ver workers usados
EXPLAIN (ANALYZE, BUFFERS) 
CREATE INDEX idx_test ON contacts USING GIN (to_tsvector('spanish', message));
```

## Collation y Unicode 16.0

Unicode actualizado a 16.0. Includes better case mapping para español.

**Relacion con analytics**: `to_tsvector('spanish', message)` para full-text search funciona mejor con stemming en espanol.

## Nuevas Funciones de String + Math

- `casefold(text)` — case-insensitive matching sofisticado
- `reverse(bytea)` — invierte bytes
- `crc32(data)`, `crc32c(data)` — checksums
- `gamma(x)`, `lgamma(x)` — funciones matematicas

**Poco relevante para tu caso**, pero utiles para validacion de datos de entrada.

---

## Resumen: que usar en tu proyecto

| Feature | Usar? | Razon |
|---------|-------|-------|
| AIO | ✅ Auto | Batch INSERT/VACUUM mas rapido |
| Virtual generated columns | ✅ Si aplica | Campos derivados sin storage |
| UUIDv7 | ✅ Obligatorio | PKs en todas las tablas |
| Skip scan | ✅ Auto con index multicolumna | Queries sin WHERE fecha |
| RETURNING OLD/NEW | ✅ Recomendado | Audit de Lambda processor |
| BRIN indexes | ❌ Ahora no | Tabla aun pequena para BRIN |
| Parallel GIN | ✅ Auto | CREATE INDEX mas rapido |
| Temporal constraints | ✅ Opcional | Si necesitas verificar no-overlaps |

---

## Referencias

- [PostgreSQL 18 Release Notes](https://www.postgresql.org/docs/release/18.0/)
- [What's New in PostgreSQL 18 (Neon Blog)](https://neon.com/postgresql/postgresql-18-new-features)
- [PostgreSQL 18: The AIO Revolution (Medium)](https://medium.com/@MattLeads/postgresql-18-the-aio-revolution-uuidv7-and-the-path-to-unprecedented-performance-6efaaee2bd72)
