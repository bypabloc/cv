# Schema design: 4 tablas para analytics

> Diseno SQL del portfolio. 4 esquemas independientes: contactos normalizados, tracking raw, agregaciones diarias, metricas diarias.

**Verificado**: 2026-05-14

[← PG18 features](./01-pg18-features-for-analytics.md) | [README](./README.md) | [Siguiente: Indexes →](./03-indexes-strategy.md)

## Arquitectura conceptual

```
DynamoDB (recoleccion cruda)
    ↓
Lambda processor
    ↓
PostgreSQL 18 (4 esquemas)
    │
    ├─ contacts (normalizada)         [fila: 1 contacto]
    ├─ tracking_events (raw)          [fila: 1 page view]
    ├─ tracking_daily_aggregates      [fila: 1 dia + pagina + utm]
    └─ daily_metrics                  [fila: 1 dia con contadores]
```

## 1. Tabla `contacts` (normalizada, ~200/mes)

```sql
CREATE TABLE contacts (
  -- Primary key
  id UUID PRIMARY KEY DEFAULT uuidv7(),

  -- Metadata
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

  -- Persona
  email VARCHAR(254) NOT NULL UNIQUE,
  first_name VARCHAR(100),
  last_name VARCHAR(100),

  -- Mensaje
  message TEXT NOT NULL,
  message_length INT GENERATED ALWAYS AS (length(message)) VIRTUAL,

  -- Originales
  service_type VARCHAR(20) NOT NULL
    CHECK (service_type IN ('hiring', 'project', 'consultation', 'interview', 'other')),
  niche VARCHAR(50) NOT NULL
    CHECK (niche IN ('generic', 'fintech', 'architect', 'leader', 'vibe')),

  -- A/B test metadata
  metadata JSONB DEFAULT '{}'::JSONB,
    -- Ejemplos: {"utm_source": "email", "device": "mobile", "referrer": "..."}

  -- Control
  is_spam BOOLEAN DEFAULT FALSE,
  processed BOOLEAN DEFAULT FALSE,
  processing_error TEXT
);

-- Constraints
ALTER TABLE contacts ADD CONSTRAINT ck_non_empty_message
  CHECK (length(trim(message)) > 0);

CREATE INDEX idx_contacts_created_at ON contacts(created_at DESC);
CREATE INDEX idx_contacts_email ON contacts(email);
CREATE INDEX idx_contacts_niche ON contacts(niche);
CREATE INDEX idx_contacts_service_type ON contacts(service_type);

-- Full-text search en message (ver seccion indexes)
CREATE INDEX idx_contacts_message_fts ON contacts USING GIN (
  to_tsvector('spanish', message)
);

-- GIN en JSONB (si quieres queries como metadata @> '{"device": "mobile"}')
CREATE INDEX idx_contacts_metadata ON contacts USING GIN (metadata jsonb_path_ops);
```

**Notas**:
- `email` UNIQUE para evitar duplicados
- `metadata JSONB` para campos que cambian sin schema migration
- Full-text search en español (stemming: "contactar" = "contacto")

## 2. Tabla `tracking_events` (raw, ~15k/mes, **particionada por mes**)

```sql
CREATE TABLE tracking_events (
  -- Primary key
  id UUID PRIMARY KEY DEFAULT uuidv7(),

  -- Tiempo (partition key)
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

  -- Identificacion de sesion
  session_id VARCHAR(128) NOT NULL,  -- de cookie o localStorage
  user_agent TEXT,
  ip_address INET,

  -- Pagina
  page_path VARCHAR(500) NOT NULL,
  page_title VARCHAR(200),
  referrer VARCHAR(500),

  -- UTM (marketing attribution)
  utm_source VARCHAR(100),
  utm_medium VARCHAR(100),
  utm_campaign VARCHAR(100),
  utm_content VARCHAR(100),

  -- Duracion
  time_on_page_seconds INT DEFAULT 0,

  -- Custom data
  extra JSONB DEFAULT '{}'::JSONB,
    -- Ejemplos: {"device": "desktop", "browser": "chrome", "country": "CL"}

  -- Control
  processed BOOLEAN DEFAULT FALSE
)
PARTITION BY RANGE (created_at);

-- Crear particiones por mes (manuales hoy, auto con pg_partman futuro)
CREATE TABLE tracking_events_2026_01 PARTITION OF tracking_events
  FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE tracking_events_2026_02 PARTITION OF tracking_events
  FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- ... continuar hasta hoy ...

-- Indexes en partition parent (hereda en hijas)
CREATE INDEX idx_tracking_events_created_at ON tracking_events(created_at DESC);
CREATE INDEX idx_tracking_events_session_id ON tracking_events(session_id);
CREATE INDEX idx_tracking_events_page_path ON tracking_events(page_path);
CREATE INDEX idx_tracking_events_utm_source ON tracking_events(utm_source);

-- Multicolumna para queries tipo "pages por dia"
CREATE INDEX idx_tracking_events_date_page ON tracking_events(
  date_trunc('day', created_at), page_path
);

-- GIN en JSONB para device/browser/country
CREATE INDEX idx_tracking_events_extra ON tracking_events USING GIN (
  extra jsonb_path_ops
);
```

**Partitioning strategy**:
- RANGE por month (created_at)
- Al final del mes, crear partition siguiente
- Al mes 60, DROP la partition mas vieja (~1ms vs DELETE lento)

## 3. Tabla `tracking_daily_aggregates` (pre-computada, ~90/mes)

```sql
CREATE TABLE tracking_daily_aggregates (
  -- Composite PK
  date DATE NOT NULL,
  page_path VARCHAR(500) NOT NULL,
  utm_source VARCHAR(100),

  PRIMARY KEY (date, page_path, utm_source),

  -- Contadores
  unique_sessions INT NOT NULL DEFAULT 0,
  page_views INT NOT NULL DEFAULT 0,
  time_on_page_avg INT NOT NULL DEFAULT 0,  -- segundos
  bounce_rate DECIMAL(5, 2) NOT NULL DEFAULT 0.0,  -- porcentaje

  -- Metadata
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_fresh BOOLEAN DEFAULT TRUE  -- si recibio update hoy
);

-- Indexes para queries frecuentes
CREATE INDEX idx_daily_agg_date ON tracking_daily_aggregates(date DESC);
CREATE INDEX idx_daily_agg_page ON tracking_daily_aggregates(page_path);
CREATE INDEX idx_daily_agg_utm ON tracking_daily_aggregates(utm_source);
```

**Notas**:
- Computada 1x diario via Lambda cron (ver materialized-views.md)
- Queries de dashboard leen AQUI, no de `tracking_events`
- Retention: borrar registros > 1 año si quieres (opcional)

## 4. Tabla `daily_metrics` (1 fila/dia, ~365/ano)

```sql
CREATE TABLE daily_metrics (
  -- Composite PK
  date DATE NOT NULL UNIQUE,
  PRIMARY KEY (date),

  -- Contactos
  contacts_total INT NOT NULL DEFAULT 0,
  contacts_new INT NOT NULL DEFAULT 0,
  contacts_by_service JSONB,  -- {"hiring": 5, "project": 3, ...}
  contacts_by_niche JSONB,    -- {"fintech": 2, "generic": 6, ...}

  -- Tracking
  unique_sessions INT NOT NULL DEFAULT 0,
  page_views_total INT NOT NULL DEFAULT 0,
  avg_session_duration INT NOT NULL DEFAULT 0,  -- segundos

  -- Conversion
  conversion_rate DECIMAL(5, 2) NOT NULL DEFAULT 0.0,  -- % (contacts / sessions)
  bounce_rate_avg DECIMAL(5, 2) NOT NULL DEFAULT 0.0,

  -- Top pages (JSONB array)
  top_pages JSONB,  -- [{"path": "/portfolio", "views": 450}, ...]
  top_referrers JSONB,

  -- Control
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index por fecha (para historicos)
CREATE INDEX idx_daily_metrics_date ON daily_metrics(date DESC);
```

**Llenado**: 1x diario via Lambda cron, usando queries de 08-queries-dashboard.md.

## ER Diagram (ASCII)

```
                    contacts
                   ┌────────┐
                   │  id (PK)
                   │  email
                   │  first_name
                   │  last_name
                   │  message
                   │  service_type (enum)
                   │  niche (enum)
                   │  metadata (JSONB)
                   │  created_at
                   └────────┘
                      ↑
                      │ (referenced by daily_metrics.contacts_by_niche)
                      │
           tracking_events (PARTITIONED)
          ┌──────────────────────────────┐
          │  id (PK)                     │
          │  created_at (partition key) │
          │  session_id                 │
          │  page_path                  │
          │  page_title                 │
          │  utm_source / medium        │
          │  utm_campaign / content     │
          │  user_agent                 │
          │  ip_address                 │
          │  time_on_page_seconds       │
          │  extra (JSONB)              │
          │  processed (BOOLEAN)        │
          └──────────────────────────────┘
              ↓ (aggregated to)
    tracking_daily_aggregates
    ┌────────────────────────────┐
    │  date                      │
    │  page_path           (PK)  │
    │  utm_source          (PK)  │
    │  unique_sessions           │
    │  page_views                │
    │  time_on_page_avg          │
    │  bounce_rate               │
    └────────────────────────────┘
        ↓ (summarized to)
        daily_metrics
        ┌──────────────────┐
        │  date        (PK)│
        │  contacts_total  │
        │  unique_sessions │
        │  conversion_rate │
        │  top_pages (JSON)│
        │  top_referrers   │
        └──────────────────┘
```

## Data flow: Lambda -> PG

```python
# Lambda processor (pseudocodigo)
import psycopg
from datetime import datetime

conn = psycopg.connect("postgresql://neon-connection-string")

# 1. Insertar contacto (de form)
conn.execute("""
  INSERT INTO contacts (email, first_name, last_name, message, service_type, niche)
  VALUES (%s, %s, %s, %s, %s, %s)
  RETURNING id, created_at
""", (email, first_name, last_name, message, service_type, niche))

# 2. Insertar tracking event (del pixel)
conn.execute("""
  INSERT INTO tracking_events (
    session_id, page_path, page_title, utm_source, utm_medium, 
    utm_campaign, utm_content, time_on_page_seconds, user_agent, ip_address
  )
  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
  RETURNING id
""", (...))

conn.commit()
```

## Summary

| Tabla | Filas/mes | Retention | Indexing | Clave |
|-------|-----------|-----------|----------|-------|
| contacts | 200 | 5+ anos | email, niche, service_type, FTS message | FK virtual a daily_metrics |
| tracking_events | 15k | 60 dias via DROP | session, page, utm, date (skip scan) | Particionada por mes |
| tracking_daily_aggregates | ~90 | 1+ ano | date, page, utm | Pre-computada 1x/dia |
| daily_metrics | ~365/ano | 5+ anos | date | 1 fila/dia |

---

## Referencias

- [PostgreSQL CREATE TABLE](https://www.postgresql.org/docs/current/sql-createtable.html)
- [PostgreSQL GENERATED COLUMNS](https://www.postgresql.org/docs/current/sql-altertable.html)
- [PostgreSQL CONSTRAINTS](https://www.postgresql.org/docs/current/ddl-constraints.html)
