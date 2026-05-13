[Volver al indice](README.md) | [Siguiente: Django Integration](02-django-integration.md)

# PostgreSQL 18 - API Reference

> Referencia de features, configuracion y cambios breaking de PostgreSQL 18.

## Identificacion

| Campo | Valor |
|-------|-------|
| Version | 18.3 (ultima estable) |
| Release | 25 septiembre 2025 |
| Soporte | Hasta noviembre 2030 |
| Docker image | `postgres:18-bookworm` / `postgres:18-alpine` |
| Driver Python | psycopg3 (`psycopg[binary]>=3.2`) |

### Politica de soporte

| Version | EOL |
|---------|-----|
| PostgreSQL 18 | Nov 2030 |
| PostgreSQL 17 | Nov 2029 |
| PostgreSQL 16 | Nov 2028 |
| PostgreSQL 15 | Nov 2027 |
| PostgreSQL 14 | Nov 2026 |
| PostgreSQL 13 | EOL (nov 2025) |

## Asynchronous I/O (AIO)

Feature estrella de PostgreSQL 18. Hasta **3x mejora en lecturas** al usar I/O asincrono para operaciones de disco.

### Configuracion

```ini
# postgresql.conf
io_method = worker          # default: usa threads para I/O
# io_method = io_uring      # Linux 5.11+, mejor performance
```

| Metodo | Requisito | Performance |
|--------|-----------|-------------|
| `worker` | Cualquier OS | Buena (default) |
| `io_uring` | Linux 5.11+ | Mejor (hasta 3x en reads) |

**Nota**: `io_uring` requiere kernel Linux 5.11+ y `liburing`. En Docker con kernel del host, verificar version del host.

### Beneficios

- Read-ahead automatico para sequential scans
- Parallel I/O para queries complejas
- Reduce latencia en workloads I/O-bound
- Transparente para la aplicacion (no requiere cambios en queries)

## Virtual Generated Columns

Columnas calculadas que NO se almacenan en disco (se calculan al leer):

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    price NUMERIC(10, 2),
    tax_rate NUMERIC(4, 2) DEFAULT 0.19,
    -- Virtual: se calcula al leer, no ocupa espacio
    total NUMERIC(12, 2) GENERATED ALWAYS AS (price * (1 + tax_rate)) VIRTUAL
);

-- Stored: se almacena en disco (ya existia en PG 12+)
ALTER TABLE products ADD COLUMN
    search_text TEXT GENERATED ALWAYS AS (name || ' ' || description) STORED;
```

| Tipo | Almacenamiento | Indexable | Uso |
|------|---------------|-----------|-----|
| VIRTUAL | No (calcula al leer) | No | Campos derivados simples |
| STORED | Si (calcula al escribir) | Si | Campos que necesitan indice |

**Default en PostgreSQL 18**: Si se omite `VIRTUAL`/`STORED`, se usa `VIRTUAL`.

## uuidv7()

Funcion nativa para generar UUIDs v7 (time-ordered):

```sql
-- UUID v7: incluye timestamp, ordenable temporalmente
SELECT uuidv7();
-- Resultado: 019526a0-7b3c-7def-8123-456789abcdef

-- Como primary key
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Extraer timestamp del UUID v7
SELECT uuid_extract_timestamp('019526a0-7b3c-7def-8123-456789abcdef');
```

### uuidv7 vs uuid v4

| Aspecto | uuid v4 | uuidv7 |
|---------|---------|--------|
| Orden | Aleatorio | Temporal (cronologico) |
| Indice B-tree | Fragmentacion alta | Insert secuencial, mejor performance |
| Timestamp | No incluye | Incluye (extraible) |
| Colisiones | Improbable (122 bits) | Improbable (similar) |
| Uso recomendado | Legacy | Nuevos proyectos |

## Skip Scan

Optimizacion de B-tree index que permite "saltar" valores en el indice:

```sql
-- Indice compuesto
CREATE INDEX idx_orders_status_date ON orders (status, created_at);

-- Antes (PG 17): Full index scan si no filtras por 'status'
-- Ahora (PG 18): Skip scan salta valores unicos de 'status'
SELECT * FROM orders WHERE created_at > '2025-01-01';
-- Usa idx_orders_status_date eficientemente aunque no filtre por status
```

Util cuando la primera columna del indice tiene **baja cardinalidad** (pocos valores unicos).

## RETURNING OLD/NEW

Acceder a valores anteriores y nuevos en operaciones DML:

```sql
-- UPDATE con acceso a valores old y new
UPDATE products SET price = price * 1.10
WHERE category = 'electronics'
RETURNING
    id,
    OLD.price AS precio_anterior,
    NEW.price AS precio_nuevo;

-- DELETE con valores eliminados
DELETE FROM expired_sessions
WHERE expires_at < now()
RETURNING OLD.*;

-- Util para auditing
INSERT INTO audit_log (table_name, old_data, new_data)
SELECT 'products', row_to_json(OLD.*), row_to_json(NEW.*)
FROM (
    UPDATE products SET price = price * 1.10
    WHERE id = 1
    RETURNING OLD.*, NEW.*
) changes;
```

## OAuth 2.0 nativo

Autenticacion con providers OAuth sin extensiones externas:

```ini
# pg_hba.conf
# Autenticacion con OAuth 2.0 provider
host all all 0.0.0.0/0 oauth issuer="https://accounts.google.com" scope="openid email"
```

```ini
# postgresql.conf
oauth_providers = 'google'
oauth_provider_google_issuer = 'https://accounts.google.com'
oauth_provider_google_client_id = 'your-client-id'
oauth_provider_google_client_secret = 'your-client-secret'
```

## Breaking changes

### PGDATA en Docker

**Cambio critico**: La ruta de datos cambia en la imagen Docker oficial.

| Version | PGDATA |
|---------|--------|
| PG 17 y anterior | `/var/lib/postgresql/data` |
| PG 18 | `/var/lib/postgresql/18/docker` |

**Impacto**: Volumenes existentes con `postgres:17` no funcionan directamente con `postgres:18`.

```yaml
# docker-compose.yml - CORRECTO para PG 18
services:
  db:
    image: postgres:18-bookworm
    volumes:
      - pgdata:/var/lib/postgresql/18/docker  # nueva ruta
    environment:
      POSTGRES_PASSWORD: secret

# Alternativa: forzar ruta antigua
services:
  db:
    image: postgres:18-bookworm
    environment:
      PGDATA: /var/lib/postgresql/data  # override manual
      POSTGRES_PASSWORD: secret
    volumes:
      - pgdata:/var/lib/postgresql/data
```

### Otras deprecaciones

- `md5` authentication deprecado (usar `scram-sha-256`)
- Data checksums habilitados por defecto
- `password_encryption` default cambia a `scram-sha-256`

## Configuracion recomendada (desarrollo)

```ini
# postgresql.conf - desarrollo local
listen_addresses = '*'
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 768MB
work_mem = 16MB
maintenance_work_mem = 128MB

# AIO
io_method = worker

# Logging
log_statement = 'all'
log_duration = on
log_min_duration_statement = 100  # ms

# Autenticacion
password_encryption = 'scram-sha-256'
```

## psycopg3 connection

```python
import psycopg
from psycopg.rows import dict_row

# Conexion sincrona
conn = psycopg.connect(
    "host=localhost dbname=mydb user=postgres password=secret",
    row_factory=dict_row,
)

# Conexion asincrona
import asyncio

async def query():
    aconn = await psycopg.AsyncConnection.connect(
        "host=localhost dbname=mydb user=postgres password=secret",
        row_factory=dict_row,
    )
    async with aconn.cursor() as cur:
        await cur.execute("SELECT * FROM products WHERE id = %s", [1])
        row = await cur.fetchone()
        return row

# Connection pool
from psycopg_pool import ConnectionPool

pool = ConnectionPool(
    "host=localhost dbname=mydb user=postgres password=secret",
    min_size=4,
    max_size=10,
)
with pool.connection() as conn:
    conn.execute("SELECT 1")
```

---

[Volver al indice](README.md) | [Siguiente: Django Integration](02-django-integration.md)
