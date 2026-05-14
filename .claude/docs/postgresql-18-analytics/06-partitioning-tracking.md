# Range partitioning para tracking_events

> Como particionar `tracking_events` por mes y limpiar datos con DROP PARTITION (ms) en lugar de DELETE (minutos).

**Verificado**: 2026-05-14

[← Materialized views](./05-materialized-views.md) | [README](./README.md) | [Siguiente: JSONB →](./07-jsonb-flexible-fields.md)

## Concepto: RANGE partitioning

Tabla grande (`tracking_events`, ~500 filas/dia) se divide en particiones por rango de fechas.

```
tracking_events (parent table)
  ├─ tracking_events_2026_01 (2026-01-01 to 2026-02-01)
  ├─ tracking_events_2026_02 (2026-02-01 to 2026-03-01)
  ├─ tracking_events_2026_03 (2026-03-01 to 2026-04-01)
  └─ ... (mas particiones)
```

**Beneficios**:
- DELETE de 60 dias = `DROP tracking_events_2026_01` (~1ms)
- vs DELETE sin partition (~5-10 segundos + VACUUM aftermath)
- Queries "ultimos 7 dias" saltean particiones viejas (pruning)
- Indexes en cada partition (menos compete entre keys)

## Crear tabla con partitioning

```sql
CREATE TABLE tracking_events (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  session_id VARCHAR(128) NOT NULL,
  page_path VARCHAR(500) NOT NULL,
  page_title VARCHAR(200),
  referrer VARCHAR(500),
  utm_source VARCHAR(100),
  utm_medium VARCHAR(100),
  utm_campaign VARCHAR(100),
  utm_content VARCHAR(100),
  time_on_page_seconds INT DEFAULT 0,
  user_agent TEXT,
  ip_address INET,
  extra JSONB DEFAULT '{}'::JSONB,
  processed BOOLEAN DEFAULT FALSE
)
PARTITION BY RANGE (created_at);
-- NOTA: PK no es permitido en tabla parent si tiene particiones
-- (PKs van en cada child partition)
```

**Alternativa**: Si quieres PK compuesto con data custom:
```sql
-- Si usas COMPOSITE key (no UUID solo), ejemplo:
CREATE TABLE tracking_events (
  id BIGSERIAL,
  created_at TIMESTAMP NOT NULL,
  session_id VARCHAR(128) NOT NULL,
  ...
  PRIMARY KEY (id, created_at)  -- created_at DEBE ser parte del PK
)
PARTITION BY RANGE (created_at);
```

## Crear particiones por mes (manualmente)

```sql
-- 2026-01
CREATE TABLE tracking_events_2026_01 PARTITION OF tracking_events
  FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- 2026-02
CREATE TABLE tracking_events_2026_02 PARTITION OF tracking_events
  FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- 2026-03
CREATE TABLE tracking_events_2026_03 PARTITION OF tracking_events
  FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');

-- ... continuar hasta hoy + 1 mes forward ...

-- 2026-05 (futuro, para inserciones que lleguen rapido)
CREATE TABLE tracking_events_2026_05 PARTITION OF tracking_events
  FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');

-- 2026-06 (muy futuro)
CREATE TABLE tracking_events_2026_06 PARTITION OF tracking_events
  FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
```

## Indexes en parent (heredan en hijas)

```sql
-- Indexes creados en parent se replican en todas las particiones
CREATE INDEX idx_tracking_created_at ON tracking_events(created_at DESC);
CREATE INDEX idx_tracking_session_id ON tracking_events(session_id);
CREATE INDEX idx_tracking_page_path ON tracking_events(page_path);
CREATE INDEX idx_tracking_utm_source ON tracking_events(utm_source);
CREATE INDEX idx_tracking_date_page ON tracking_events(
  DATE_TRUNC('day', created_at), page_path, utm_source
);
CREATE INDEX idx_tracking_extra ON tracking_events USING GIN (extra jsonb_path_ops);

-- Ver indexes en partition
SELECT indexname FROM pg_indexes 
WHERE tablename = 'tracking_events_2026_01'
ORDER BY indexname;
```

## Insertar en tabla particionada

Sin cambios en codigo Lambda:

```python
# Python / psycopg3
import psycopg
from datetime import datetime

conn = psycopg.connect("postgresql://...")

# INSERT automaticamente elige la partition correcta
conn.execute("""
  INSERT INTO tracking_events (
    session_id, page_path, page_title, utm_source, time_on_page_seconds, extra
  )
  VALUES (%s, %s, %s, %s, %s, %s)
""", (session_id, page_path, page_title, utm_source, 45, {'device': 'mobile'}))

conn.commit()
# PostgreSQL elige partition_2026_05 automaticamente si created_at ~ ahora
```

## Retencion: DROP partition vieja cada mes

### Opcion 1: pg_cron (scheduled, automatic)

```sql
-- Job que corre el 1 de cada mes a las 4 AM
SELECT cron.schedule(
  'drop_old_tracking_partition',
  '0 4 1 * *',  -- 1st day of month, 4 AM UTC
  $$
  DO $$
  DECLARE
    partition_name TEXT;
  BEGIN
    partition_name := 'tracking_events_' || TO_CHAR(CURRENT_DATE - INTERVAL '60 days', 'YYYY_MM');
    EXECUTE 'DROP TABLE IF EXISTS ' || partition_name;
    RAISE NOTICE 'Dropped partition: %', partition_name;
  END $$;
  $$
);
```

### Opcion 2: Lambda external (mas control)

```python
# Lambda triggered monthly (EventBridge rule: "0 4 1 * ?")
import psycopg
import os
from datetime import datetime, timedelta

def handler(event, context):
    conn = psycopg.connect(os.environ['DATABASE_URL'])
    
    # Calcular fecha de 60 dias atras
    cutoff_date = datetime.now() - timedelta(days=60)
    partition_to_drop = f"tracking_events_{cutoff_date.strftime('%Y_%m')}"
    
    try:
        conn.execute(f"DROP TABLE IF EXISTS {partition_to_drop} CASCADE")
        conn.commit()
        print(f"Dropped partition: {partition_to_drop}")
        return {'statusCode': 200}
    except Exception as e:
        print(f"Error dropping partition: {e}")
        conn.rollback()
        return {'statusCode': 500, 'error': str(e)}
    finally:
        conn.close()
```

## DETACH vs DROP

| Operacion | Efecto | Uso |
|-----------|--------|-----|
| DROP TABLE | Borra datos permanentemente | Purga final |
| DETACH PARTITION | Desvincula de parent, mantiene tabla | Exportar antes de borrar |

**Workflow con DETACH**:
```sql
-- Step 1: Detach (sin eliminar datos)
ALTER TABLE tracking_events DETACH PARTITION tracking_events_2025_06;

-- Step 2: Exportar a CSV (backup)
COPY tracking_events_2025_06 TO '/tmp/tracking_2025_06.csv' WITH CSV;

-- Step 3: Eliminar
DROP TABLE tracking_events_2025_06;
```

## Queries con partition pruning

PostgreSQL **poda** particiones automaticamente si la query tiene WHERE en la partition key.

```sql
-- BUENO: accede solo a tracking_events_2026_05
EXPLAIN ANALYZE
SELECT * FROM tracking_events
WHERE created_at >= '2026-05-01' AND created_at < '2026-05-02';
-- Plan: Seq Scan on tracking_events_2026_05

-- MALO: accede TODAS las particiones
EXPLAIN ANALYZE
SELECT * FROM tracking_events
WHERE page_path = '/portfolio';
-- Plan: Seq Scan on tracking_events_2026_01, Seq Scan on tracking_events_2026_02, ...

-- MEJOR: agregar FILTER en created_at aunque sea range amplio
EXPLAIN ANALYZE
SELECT * FROM tracking_events
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
  AND page_path = '/portfolio';
-- Plan: Seq Scan on tracking_events_2026_04, Seq Scan on tracking_events_2026_05
-- (solo 2 partitions!)
```

## Crear partition nuevas dynamicamente

### Opcion 1: Procedure PL/pgSQL (on demand)

```sql
CREATE OR REPLACE FUNCTION create_tracking_partition(
  p_month DATE
)
RETURNS VOID AS $$
DECLARE
  partition_name TEXT;
  start_date DATE;
  end_date DATE;
BEGIN
  start_date := DATE_TRUNC('month', p_month)::DATE;
  end_date := start_date + INTERVAL '1 month'::INTERVAL;
  partition_name := 'tracking_events_' || TO_CHAR(start_date, 'YYYY_MM');
  
  -- Evitar duplicados
  IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = partition_name) THEN
    EXECUTE FORMAT(
      'CREATE TABLE %I PARTITION OF tracking_events FOR VALUES FROM (%L) TO (%L)',
      partition_name, start_date, end_date
    );
    RAISE NOTICE 'Created partition: %', partition_name;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Usar
SELECT create_tracking_partition('2026-06-01'::DATE);
SELECT create_tracking_partition('2026-07-01'::DATE);
```

### Opcion 2: pg_partman extension (auto)

```sql
-- Instalar extension (en Neon, puede requerir request)
CREATE EXTENSION IF NOT EXISTS pg_partman;

-- Configurar tabla para auto-partitioning
SELECT partman.create_parent(
  p_parent_table => 'public.tracking_events',
  p_control => 'created_at',
  p_type => 'range',
  p_interval => '1 month',
  p_premake => 2  -- crear 2 meses forward
);

-- Crear job de mantenimiento
SELECT cron.schedule(
  'maintain_tracking_partitions',
  '0 */4 * * *',  -- cada 4 horas
  'SELECT partman.maintain_partition_trigger(''public.tracking_events'')'
);
```

## Monitoreo de partitions

```sql
-- Ver todas las partitions
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE tablename LIKE 'tracking_events_%'
ORDER BY tablename;

-- Ver cantidad de rows por partition
SELECT
  schemaname,
  tablename,
  n_live_tup AS row_count
FROM pg_stat_user_tables
WHERE tablename LIKE 'tracking_events_%'
ORDER BY tablename;

-- Ver partitions que estan vacias (candidatas a drop)
SELECT
  tablename,
  n_live_tup
FROM pg_stat_user_tables
WHERE tablename LIKE 'tracking_events_%'
  AND n_live_tup = 0
ORDER BY tablename;
```

## Benchmarks esperados

| Operacion | Sin partition | Con partition |
|-----------|---------------|---------------|
| INSERT 1000 filas | 50ms | 40ms (index routing overhead minimo) |
| DELETE/DROP de 60 dias | ~5 segundos | ~1ms |
| Query "ultimos 7 dias" | 500ms (scan all) | 50ms (prune 11/12 partitions) |
| VACUUM full | 10 segundos | 50ms (una partition) |

---

## Checklist: crear partitioned table

- [ ] CREATE TABLE con `PARTITION BY RANGE (created_at)`
- [ ] Crear partitions manuales para ultimos 3 meses + futuro 2 meses
- [ ] Crear indexes en parent (heredan en hijas)
- [ ] Setup pg_cron drop job o Lambda retention Lambda
- [ ] Test INSERT, verificar routing correcto con `SELECT table_name FROM pg_class ...`
- [ ] Test DROP, verificar < 10ms
- [ ] Monitorear `pg_stat_user_tables` primeros 30 dias

---

## Referencias

- [PostgreSQL Table Partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- [Time-based Retention Strategies in Postgres (Sequin)](https://blog.sequinstream.com/time-based-retention-strategies-in-postgres/)
- [Auto-archiving with pg_partman (Crunchy Data)](https://www.crunchydata.com/blog/auto-archiving-and-data-retention-management-in-postgres-with-pg_partman)
