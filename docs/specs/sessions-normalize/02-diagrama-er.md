# 02 — Diagrama ER + schema SQL

[← Contexto](01-contexto-y-decisiones.md) | [Siguiente: Archivos afectados →](03-archivos-afectados.md)

## ER (ASCII inline)

```
                                                       event_types
                                                       │ id (UUID, PK)
                                                       │ code_name (UNIQUE)
                                                       │ description
                                                       │ created_at
                                                       └──┐
                                                          │
                                                          │ FK event_type_id
                                                          ▼
sessions                       session_visits           tracking_events
│ session_id  (TEXT, PK)       │ visit_id  (UUID, PK)   │ session_id  (TEXT, FK)
│ first_seen_at                │ session_id (TEXT, FK)  │ visit_id    (UUID, FK)
│ last_seen_at                 │ started_at             │ page_id     (UUID)
│ user_agent                   │ ended_at               │ created_at
│ browser                      │ ip                     │ received_at
│ browser_version              │ country                │ page_path
│ os                           │ utm_source             │ event_id
│ device_type                  │ utm_medium             │ event_type_id
└──┐                           │ utm_campaign           │ event_props
   │                           │ utm_content            │ viewport_width
   │ FK session_id (1:N)       │ utm_term               │ viewport_height
   ├──────────────────────►   │ referrer               │ niche
   │                           │ landing_page_path      └──────────────
   │                           │ niche
   │                           └──┐
   │                              │ FK visit_id (1:N)
   │                              ├──────────────────► (tracking_events.visit_id)
   │
   │
   │ FK session_id (1:N)
   │
   ▼
contacts
│ id  (UUID, PK)
│ session_id  (TEXT, FK, NOT NULL)
│ created_at, received_at
│ name, email (CITEXT), message
│ company, role, service_type, budget, timeline, niche
│ status, notes
└──────────────
```

Leyenda:

- `──►` FK (la flecha apunta a la tabla referenciada)
- Sin cascade — un DELETE en `sessions` falla si tiene visits, events o
  contacts (decision 7).

## Schema SQL (estado final post-migracion)

### `sessions`

```sql
CREATE TABLE sessions (
    session_id      TEXT PRIMARY KEY,
    first_seen_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_agent      TEXT,
    browser         TEXT,
    browser_version TEXT,
    os              TEXT,
    device_type     TEXT
);

-- Indices
CREATE INDEX idx_sessions_first_seen_brin
  ON sessions USING brin (first_seen_at);
CREATE INDEX idx_sessions_last_seen
  ON sessions (last_seen_at DESC);
```

### `session_visits`

```sql
CREATE TABLE session_visits (
    visit_id          UUID PRIMARY KEY DEFAULT uuidv7(),
    session_id        TEXT NOT NULL REFERENCES sessions(session_id),
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    ip                INET,
    country           CHAR(2),
    utm_source        TEXT,
    utm_medium        TEXT,
    utm_campaign      TEXT,
    utm_content       TEXT,
    utm_term          TEXT,
    referrer          TEXT,
    landing_page_path TEXT,
    niche             TEXT
);

-- Indices: query "ultimo visit del session" + analitica multi-touch
CREATE INDEX idx_visits_session_started
  ON session_visits (session_id, started_at DESC);
CREATE INDEX idx_visits_started_brin
  ON session_visits USING brin (started_at);
CREATE INDEX idx_visits_country
  ON session_visits (country) WHERE country IS NOT NULL;
CREATE INDEX idx_visits_niche
  ON session_visits (niche) WHERE niche IS NOT NULL;
CREATE INDEX idx_visits_utm_source
  ON session_visits (utm_source) WHERE utm_source IS NOT NULL;
```

### `tracking_events` (modificada)

```sql
-- DROPS aplicados por la migracion:
ALTER TABLE tracking_events
  DROP COLUMN ip,
  DROP COLUMN country,
  DROP COLUMN user_agent,
  DROP COLUMN browser,
  DROP COLUMN browser_version,
  DROP COLUMN os,
  DROP COLUMN device_type,
  DROP COLUMN utm_source,
  DROP COLUMN utm_medium,
  DROP COLUMN utm_campaign,
  DROP COLUMN utm_content,
  DROP COLUMN utm_term;

-- Nueva columna visit_id + FKs
ALTER TABLE tracking_events
  ADD COLUMN visit_id UUID;
-- TRUNCATE garantiza que no hay rows; ahora se puede poner NOT NULL.
ALTER TABLE tracking_events
  ALTER COLUMN visit_id SET NOT NULL,
  ALTER COLUMN session_id SET NOT NULL;
ALTER TABLE tracking_events
  ADD CONSTRAINT fk_tracking_events_session
    FOREIGN KEY (session_id) REFERENCES sessions(session_id);
ALTER TABLE tracking_events
  ADD CONSTRAINT fk_tracking_events_visit
    FOREIGN KEY (visit_id) REFERENCES session_visits(visit_id);

-- Indices que se eliminan porque las columnas desaparecen:
DROP INDEX IF EXISTS idx_tracking_utm_source;
DROP INDEX IF EXISTS idx_tracking_country;
DROP INDEX IF EXISTS idx_tracking_device_type;

-- Indice nuevo
CREATE INDEX idx_tracking_visit_id ON tracking_events (visit_id);
```

Columnas finales de `tracking_events`: `session_id`, `visit_id`,
`page_id`, `created_at`, `received_at`, `page_path`, `event_id`,
`event_type_id`, `event_props`, `viewport_width`, `viewport_height`,
`niche`.

### `contacts` (modificada)

```sql
ALTER TABLE contacts
  DROP COLUMN ip,
  DROP COLUMN country,
  DROP COLUMN user_agent;

-- TRUNCATE -> ahora se puede poner NOT NULL
ALTER TABLE contacts
  ALTER COLUMN session_id SET NOT NULL;

ALTER TABLE contacts
  ADD CONSTRAINT fk_contacts_session
    FOREIGN KEY (session_id) REFERENCES sessions(session_id);

-- Indice idx_contacts_session_id ya existe (parcial WHERE NOT NULL);
-- se recrea sin el WHERE (ya no es nullable).
DROP INDEX IF EXISTS idx_contacts_session_id;
CREATE INDEX idx_contacts_session_id ON contacts (session_id);
```

## Tipos validos (resumen)

- `TEXT`, `CHAR(2)`, `INET`, `UUID`, `TIMESTAMPTZ`, `INTEGER`, `JSONB`,
  `CITEXT` (solo en `contacts.email`).

## Relaciones

- `sessions` 1:N `session_visits` (FK `session_visits.session_id`)
- `sessions` 1:N `tracking_events` (FK `tracking_events.session_id`)
- `session_visits` 1:N `tracking_events` (FK `tracking_events.visit_id`)
- `sessions` 1:N `contacts` (FK `contacts.session_id`)
- `event_types` 1:N `tracking_events` (existente — sin cambios)

## Sobre el particionado

`tracking_events` esta particionada por `RANGE(created_at)` con
particion default `tracking_events_default`. La migracion respeta el
particionado: los `ALTER TABLE` con `DROP COLUMN` se propagan
automaticamente a las particiones en PG14+. El `ALTER TABLE ... ADD
CONSTRAINT FOREIGN KEY` tambien se propaga (PG12+).

`sessions` y `session_visits` NO se particionan: su cardinalidad es
mucho menor (1 row por session vs. N rows por evento).

[← Contexto](01-contexto-y-decisiones.md) | [Siguiente: Archivos afectados →](03-archivos-afectados.md)
