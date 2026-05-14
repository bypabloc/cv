# JSONB para campos flexibles

> Cuando usar JSONB, como indexar con GIN, operadores, y anti-patterns comunes.

**Verificado**: 2026-05-14

[← Partitioning](./06-partitioning-tracking.md) | [README](./README.md) | [Siguiente: Dashboard queries →](./08-queries-dashboard.md)

## Cuando usar JSONB

**Bueno**: Campos que cambian sin schema migration
- `contacts.metadata`: utm_source, device, referrer enriquecidos, A/B test variant
- `tracking_events.extra`: device/browser/country derivados, custom events
- Audit trails: "campo X cambio de A a B a las 10:15"

**Malo**: Usarlo cuando sabes la estructura y es estable
- `message` debe ser TEXT, no JSONB
- `utm_source` debe ser VARCHAR(100), no `metadata->>'utm_source'`

## Ejemplos de uso

### Insertar datos con JSONB

```python
# Python / psycopg3
conn.execute("""
  INSERT INTO contacts (email, message, metadata)
  VALUES (%s, %s, %s)
""", (
  'user@example.com',
  'Hola, me interesa...',
  {
    'utm_source': 'email',
    'utm_campaign': 'launch-2026',
    'device': 'mobile',
    'browser': 'chrome',
    'referrer': 'https://newsletter.example.com',
    'ip': '203.0.113.45',
    'session_id': 'abc-123-def'
  }
))
```

### Queries simples (operadores JSONB)

```sql
-- Acceder a un campo: ->
SELECT
  email,
  metadata->>'utm_source' AS utm_source
FROM contacts
LIMIT 5;

-- Filtrar por existencia de campo: ?
SELECT COUNT(*) FROM contacts
WHERE metadata ? 'utm_source';

-- Filtrar por valor especifico: ->>
SELECT COUNT(*) FROM contacts
WHERE metadata->>'device' = 'mobile';

-- Contains (@>): metadata tiene ambos campos
SELECT COUNT(*) FROM contacts
WHERE metadata @> '{"device": "mobile", "browser": "chrome"}';

-- Key exists (?|): campo es uno de varios
SELECT COUNT(*) FROM contacts
WHERE metadata ?| array['utm_source', 'utm_campaign'];
```

## Indexing JSONB: GIN

```sql
-- Opcion 1: jsonb_path_ops (mas eficiente, recomendado)
CREATE INDEX idx_contacts_metadata ON contacts USING GIN (
  metadata jsonb_path_ops
);

-- Opcion 2: jsonb_ops (default, mas flexibilidad, mas lento)
CREATE INDEX idx_contacts_metadata_ops ON contacts USING GIN (
  metadata
);
```

### Diferencia: jsonb_path_ops vs jsonb_ops

| Operacion | jsonb_ops | jsonb_path_ops |
|-----------|-----------|---|
| `metadata @> '{"device": "mobile"}'` | ✅ | ✅ |
| `metadata ? 'device'` | ✅ | ❌ |
| `metadata ->> 'device'` (sin index) | ✅ | ✅ |
| Size | ~5MB | ~1MB |
| Build time | 10s | 5s |
| Update overhead | Alto | Bajo |

**Recomendacion**: Usa `jsonb_path_ops` para analytics (read-heavy, optimizado para `@>`).

## Queries de analytics con JSONB

### Por device (mobile vs desktop)

```sql
SELECT
  metadata->>'device' AS device,
  COUNT(*) AS contact_count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM contacts
WHERE metadata->>'device' IS NOT NULL
GROUP BY metadata->>'device'
ORDER BY contact_count DESC;

-- Resultado:
-- device | contact_count | pct
-- mobile | 142           | 71.00
-- desktop| 58            | 29.00
```

### Por UTM source (email, social, direct)

```sql
SELECT
  metadata->>'utm_source' AS utm_source,
  metadata->>'utm_campaign' AS utm_campaign,
  COUNT(*) AS conversions,
  ROUND(AVG(CHAR_LENGTH(message))::NUMERIC, 0) AS avg_message_length
FROM contacts
WHERE metadata->>'utm_source' IS NOT NULL
GROUP BY metadata->>'utm_source', metadata->>'utm_campaign'
ORDER BY conversions DESC;
```

### Audit trail: registrar cambios

```sql
CREATE TABLE contacts_audit (
  id BIGSERIAL PRIMARY KEY,
  contact_id UUID NOT NULL,
  change JSONB NOT NULL,  -- {"field": "message", "old_value": "...", "new_value": "..."}
  changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar cambio
INSERT INTO contacts_audit (contact_id, change)
VALUES (
  '550e8400-e29b-41d4-a716-446655440000'::UUID,
  '{"field": "message", "old_value": "antes", "new_value": "despues"}'::JSONB
);

-- Query audit trail de un contacto
SELECT
  change->>'field' AS field_changed,
  change->>'old_value' AS old_val,
  change->>'new_value' AS new_val,
  changed_at
FROM contacts_audit
WHERE contact_id = '550e8400-e29b-41d4-a716-446655440000'::UUID
ORDER BY changed_at DESC;
```

## Anti-patterns (EVITAR)

### 1. Guardar TODO en JSONB

**MAL**:
```python
metadata = {
  'email': 'user@example.com',  # ❌ Esto debe ser columna VARCHAR
  'first_name': 'Pablo',         # ❌ Columna separada
  'last_name': 'Contreras',      # ❌ Columna separada
  'utm_source': 'email'
}
conn.execute("INSERT INTO contacts (metadata) VALUES (%s)", (metadata,))
```

**BIEN**: Columnas estructuradas + JSONB para lo flexible
```python
conn.execute("""
  INSERT INTO contacts (email, first_name, last_name, metadata)
  VALUES (%s, %s, %s, %s)
""", (
  'user@example.com',
  'Pablo',
  'Contreras',
  {'utm_source': 'email', 'device': 'mobile'}
))
```

### 2. Olvidar CAST a tipo correcto

**MAL**:
```sql
-- Compara string con numero
SELECT COUNT(*) FROM contacts
WHERE metadata->>'zip_code' = 12345;  -- 12345 es INT, metadata es TEXT
-- Resultado: 0 (no matchea)
```

**BIEN**:
```sql
-- Cast explicito
SELECT COUNT(*) FROM contacts
WHERE CAST(metadata->>'zip_code' AS INT) = 12345;

-- O directamente en inserciones
INSERT INTO contacts_audit (change)
VALUES ('{"amount": 123.45}'::JSONB);  -- ->>'amount' sera '123.45' (string)
```

### 3. Guardar arrays en JSONB si quieres buscar elementos

**MAL**:
```sql
-- Quieres buscar contacts que tienen "python" en skills
-- Pero guardaste en array JSONB
metadata = {
  'skills': ['python', 'javascript', 'sql']
}

-- Esta query NO funciona (no hay GIN support para array search basico)
SELECT * FROM contacts
WHERE metadata->'skills' @> '"python"'::JSONB;  -- Funciona pero lento
```

**MEJOR**: Usar PostgreSQL native arrays o columna separada
```sql
-- Native array en columna separada
CREATE TABLE contacts (
  skills TEXT[] NOT NULL DEFAULT '{}',
  ...
);

-- Query rapida con GIN index
CREATE INDEX idx_contacts_skills ON contacts USING GIN (skills);
SELECT * FROM contacts WHERE skills @> ARRAY['python'];
```

### 4. Index en JSONB sin jsonb_path_ops

**MAL**:
```sql
-- jsonb_ops es default, pero menos eficiente
CREATE INDEX idx_metadata ON contacts USING GIN (metadata);
-- Size: 5MB, update overhead: Alto
```

**BIEN**:
```sql
-- jsonb_path_ops es mas pequeno y rapido
CREATE INDEX idx_metadata ON contacts USING GIN (metadata jsonb_path_ops);
-- Size: 1MB, update overhead: Bajo
```

### 5. Usar `->` (con comillas) cuando quieres `->>`

**MAL**:
```sql
SELECT metadata->'device' FROM contacts LIMIT 1;
-- Resultado: "mobile" (con comillas JSON, es JSONB type)

SELECT metadata->'device' = 'mobile' FROM contacts;
-- Resultado: FALSE siempre (comparas JSONB con TEXT)
```

**BIEN**:
```sql
SELECT metadata->>'device' FROM contacts LIMIT 1;
-- Resultado: mobile (sin comillas, es TEXT type)

SELECT metadata->>'device' = 'mobile' FROM contacts;
-- Resultado: TRUE donde aplica
```

## Performance tuning

### Ver tamanio de indexes

```sql
SELECT
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) AS size,
  idx_scan,
  idx_tup_read
FROM pg_stat_user_indexes
WHERE indexname LIKE '%metadata%'
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Ver queries lentas en JSONB

```sql
-- Queries que NO usan el index
EXPLAIN ANALYZE
SELECT COUNT(*) FROM contacts
WHERE metadata->>'device' = 'mobile';
-- Si no usa "Index Scan on idx_contacts_metadata", falta ->

-- Queries que SI usan index
EXPLAIN ANALYZE
SELECT COUNT(*) FROM contacts
WHERE metadata @> '{"device": "mobile"}';
-- Debe usar "Index Scan on idx_contacts_metadata"
```

## Migracion: columnas a JSONB

Si empezaste con columnas separadas y quieres consolidar:

```sql
-- Antes:
CREATE TABLE contacts (
  id UUID PRIMARY KEY,
  utm_source VARCHAR(100),
  utm_campaign VARCHAR(100),
  device VARCHAR(50),
  browser VARCHAR(100)
);

-- Migracion:
ALTER TABLE contacts ADD COLUMN metadata JSONB DEFAULT '{}';

UPDATE contacts SET metadata = JSONB_BUILD_OBJECT(
  'utm_source', utm_source,
  'utm_campaign', utm_campaign,
  'device', device,
  'browser', browser
)
WHERE utm_source IS NOT NULL OR device IS NOT NULL;

-- Drop columnas viejas
ALTER TABLE contacts DROP COLUMN utm_source;
ALTER TABLE contacts DROP COLUMN utm_campaign;
ALTER TABLE contacts DROP COLUMN device;
ALTER TABLE contacts DROP COLUMN browser;
```

## Summary

| Aspecto | Recomendacion |
|--------|---|
| Cuando usar | Campos variables sin schema change |
| Indexing | GIN + jsonb_path_ops |
| Operadores | `@>` para contiene, `?` para key exists |
| Cast | Explicito en queries analíticas |
| Evitar | Guardar TODO en JSONB, array searches complejas |

---

## Referencias

- [PostgreSQL JSONB Type](https://www.postgresql.org/docs/current/datatype-json.html)
- [Indexing JSONB in PostgreSQL (Crunchy Data)](https://www.crunchydata.com/blog/indexing-jsonb-in-postgres)
- [GIN Indexes Guide (Medium)](https://medium.com/@vedantthakkar1003/mastering-postgresql-gin-indexes-the-ultimate-guide-to-faster-jsonb-array-and-full-text-search-f1f8ec3e67af)
