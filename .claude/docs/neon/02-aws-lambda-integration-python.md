# AWS Lambda + Neon con psycopg3

> Integrar Neon PostgreSQL en Python 3.13 Lambdas. Connection pooling, cold start,
> y codigo real. Verificado 2026-05-14.

## Setup (5 pasos)

### 1. Neon connection string desde SSM Parameter Store

```bash
# Neon dashboard → connection string (pooled)
# Formato: postgresql://user:password@host/dbname?sslmode=require&channel_binding=require

# Guardar en SSM (mismo patron que secrets)
aws ssm put-parameter \
  --name /portfolio/neon-database-url \
  --value "postgresql://user:password@host/dbname?sslmode=require&channel_binding=require" \
  --type SecureString \
  --region us-west-2
```

Nota: usar **pooled connection string** de Neon (sufijo `-pooler`). Sin pooling, Lambdas exhaust max connections.

### 2. Lambda execution role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["ssm:GetParameter"],
      "Resource": "arn:aws:ssm:us-west-2:ACCOUNT:parameter/portfolio/neon-database-url"
    }
  ]
}
```

### 3. Layer de dependencias (psycopg3)

```bash
# Crear layer
mkdir -p python
pip install -t python psycopg[binary]  # binary para lambda runtime
zip -r psycopg3-layer.zip python
aws lambda publish-layer-version \
  --layer-name psycopg3 \
  --zip-file fileb://psycopg3-layer.zip
```

### 4. Codigo Lambda (handler)

```python
"""
Handler Lambda para escribir tracking events a Neon.
Database connection inicializado en module scope (reutilizado entre invocaciones).
"""

import json
import os
import sys
from typing import Any

import boto3
import psycopg

# Clientes AWS en module scope (reutilizables)
ssm_client = boto3.client('ssm', region_name='us-west-2')

# Placeholder para conexion (lazy-loaded)
_db_conn: psycopg.Connection | None = None


def get_database_connection() -> psycopg.Connection:
    """
    Retorna conexion a Neon (cached en module scope).
    Reutilizacion entre invocaciones = warm performance.
    """
    global _db_conn

    if _db_conn is None:
        # Leer connection string desde SSM (una sola vez por container)
        try:
            resp = ssm_client.get_parameter(
                Name='/portfolio/neon-database-url',
                WithDecryption=True,
            )
            db_url = resp['Parameter']['Value']
        except Exception as e:
            print(f'[ERROR] Failed to get DB URL from SSM: {e}')
            raise

        # Conectar a Neon (con SSL + channel binding)
        try:
            _db_conn = psycopg.connect(db_url, autocommit=True)
            print('[INFO] Connected to Neon (pooled)')
        except Exception as e:
            print(f'[ERROR] Failed to connect to Neon: {e}')
            raise

    return _db_conn


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Handler de tracking events: inserta evento en Neon.

    Ejemplo event (via DynamoDB Streams):
    {
        "contact_id": "abc123",
        "event_type": "page_visit",
        "properties": {"page": "/experience", "duration_ms": 1234},
        "timestamp": "2026-05-14T10:30:00Z"
    }
    """
    conn = get_database_connection()

    try:
        contact_id = event.get('contact_id')
        event_type = event.get('event_type')
        properties = event.get('properties', {})
        timestamp = event.get('timestamp')

        # Insertar en Neon
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO tracking_events (
                    contact_id, event_type, properties, created_at
                ) VALUES (%s, %s, %s, %s)
                ''',
                (contact_id, event_type, json.dumps(properties), timestamp),
            )
        # autocommit=True → commit automatico

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Event tracked', 'contact_id': contact_id}),
        }

    except Exception as e:
        print(f'[ERROR] Failed to track event: {e}')
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
        }


def handler_analytics(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Handler de lectura: consulta estadisticas de eventos.
    """
    conn = get_database_connection()

    try:
        with conn.cursor() as cur:
            # Query: eventos por tipo (ultimo 24h)
            cur.execute(
                '''
                SELECT event_type, COUNT(*) as count
                FROM tracking_events
                WHERE created_at > NOW() - INTERVAL '24 hours'
                GROUP BY event_type
                ORDER BY count DESC
                '''
            )
            rows = cur.fetchall()

        stats = [{'event_type': row[0], 'count': row[1]} for row in rows]

        return {
            'statusCode': 200,
            'body': json.dumps({'stats': stats}),
        }

    except Exception as e:
        print(f'[ERROR] Failed to fetch analytics: {e}')
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
        }
```

### 5. Schema en Neon

```sql
-- Ejecutar una sola vez en Neon
CREATE TABLE tracking_events (
    id BIGSERIAL PRIMARY KEY,
    contact_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_contact FOREIGN KEY (contact_id)
        REFERENCES contacts(id) ON DELETE CASCADE
);

CREATE INDEX idx_tracking_events_contact_id
    ON tracking_events(contact_id);

CREATE INDEX idx_tracking_events_created_at
    ON tracking_events(created_at DESC);

CREATE INDEX idx_tracking_events_event_type
    ON tracking_events(event_type, created_at DESC);
```

## Pooling: dos opciones

### Opcion A: Neon pooled endpoint (recomendada para Lambda)

Neon provee sufijo `-pooler` en connection string:
```
postgresql://user:password@endpoint-pooler.neon.tech/dbname
```

Usar **siempre** para Lambda (PgBouncer managed by Neon).

- Pro: sin administracion, Neon lo gestiona
- Pro: evita exhaustion de max connections
- Con: menor precision en transacciones (transaction mode, no session mode)

### Opcion B: psycopg3 connection pool (para non-Lambda, raro)

```python
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

# Pool configurado en module scope (non-Lambda)
pool: AsyncConnectionPool | None = None

async def get_pool() -> AsyncConnectionPool:
    global pool
    if pool is None:
        pool = AsyncConnectionPool(
            'postgresql://...',
            min_size=2,
            max_size=10,
            timeout=5.0,
        )
        await pool.open()
    return pool

# Usar en handler:
async def handler(...):
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(...)
```

Para portfolio (Lambdas): **opcion A (pooled endpoint)** es suficiente.

## Performance: cold start analysis

Secuencia de una invocacion:

```
Lambda init:                    ~0 ms (Neon compute suspended?)
├─ ssm_client.get_parameter()   ~100-200 ms (network to SSM)
├─ psycopg.connect()            ~150-300 ms (cold: resolve host, SSL handshake, auth)
│                               ~10-50 ms (warm: reuse connection pool)
└─ execute + fetch              ~10-100 ms (query dependent)

TOTAL cold start: ~250-500 ms
TOTAL warm start: ~50-150 ms
```

Optimization tips:

1. **Module scope para clientes**: ssm_client y db_conn en module scope (ejecuta 1 vez)
2. **Connection reuse**: handler reutiliza conexion entre invocaciones
3. **Suspended resume**: Neon auto-suspends despues 5 min. Resume cuesta ~200-500ms (uno vez)
4. **Provisioned Concurrency**: no worth para este volumen (Free tier, bajo traffic)

Para portfolio: cold start ~250-500ms es acceptable (low-frequency lambdas).

## Errores frecuentes

| Error | Causa | Fix |
|-------|-------|-----|
| `could not resolve host` | Neon compute suspendido | normal, 200-500ms resume |
| `too many connections` | No usar `-pooler` endpoint | cambiar a pooled connection string |
| `SSL certificate error` | Missing `sslmode=require` | agregar a connection string |
| `channel binding required` | Missing `channel_binding=require` | agregar a connection string |
| `Parameter not found` | SSM path incorrecto | verificar path exacto en AWS |
| `psycopg not found` | Layer no attached | verificar Layer ARN en Lambda config |

## Comparacion: psycopg3 vs psycopg2

| Aspecto | psycopg2 | psycopg3 |
|--------|----------|----------|
| Soporte | deprecated | current |
| Async | separado (`psycopg2-extras`) | nativo |
| Binary wheels | si | si |
| Cold start | ~100ms | ~150-200ms |
| Performance | estandar | equiv. o mejor |
| Future proof | ❌ | ✓ |

**Usar psycopg3** para proyecto nuevo (portfolio).

## Referencias

- [Neon AWS Lambda Guide](https://neon.com/docs/guides/aws-lambda)
- [psycopg3 Documentation](https://www.psycopg.org/psycopg3/)
- [AWS SSM Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
- [Lambda Layers](https://docs.aws.amazon.com/lambda/latest/dg/invocation-layers.html)
