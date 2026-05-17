-- Migration 001: init schema
-- Crea tablas contacts + tracking_events + processed_stream_events
-- PG18 features: UUIDv7 nativo, GeneratedField virtual, GIN, BRIN
--
-- Idempotente: usa CREATE TABLE IF NOT EXISTS

BEGIN;

-- Extensions necesarias (deben crearse ANTES de las tablas que las usan)
CREATE EXTENSION IF NOT EXISTS citext;

-- =============================================================================
-- contacts: replica de DynamoDB ContactsTable (form submissions)
-- =============================================================================
CREATE TABLE IF NOT EXISTS contacts (
    -- PK: UUIDv7 generado por la Lambda al insert (no usamos uuidv7() de PG aqui
    -- porque queremos que el id coincida con DynamoDB)
    id UUID PRIMARY KEY,

    -- Idempotency key del DynamoDB Stream event (evita doble insert)
    stream_event_id TEXT UNIQUE,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Form fields
    name TEXT NOT NULL,
    email CITEXT NOT NULL,  -- case-insensitive para CRM matching
    message TEXT NOT NULL,
    company TEXT,
    role TEXT,
    service_type TEXT CHECK (
        service_type IN ('consulting', 'fulltime', 'contract', 'other')
        OR service_type IS NULL
    ),
    budget TEXT,
    timeline TEXT,
    niche TEXT,

    -- Request metadata
    ip INET,
    country CHAR(2),
    user_agent TEXT,

    -- Marketing/lifecycle (poblado manualmente por owner)
    status TEXT DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'qualified', 'converted', 'rejected')),
    notes TEXT
);

-- =============================================================================
-- tracking_events: replica de DynamoDB TrackingTable (partitioned por mes)
-- =============================================================================
CREATE TABLE IF NOT EXISTS tracking_events (
    -- Composite PK como en DynamoDB
    session_id TEXT NOT NULL,
    page_id UUID NOT NULL,

    -- Idempotency (sin UNIQUE constraint - PG no soporta UNIQUE en partitioned
    -- table sin incluir partitioning column. Idempotency se enforce via
    -- processed_stream_events PK)
    stream_event_id TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ,  -- mirror del TTL de DynamoDB

    -- Page metadata
    page_url TEXT NOT NULL,
    page_title TEXT,
    page_path TEXT,
    referrer TEXT,

    -- UTM
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    utm_content TEXT,
    utm_term TEXT,

    -- Viewport
    viewport_width INT,
    viewport_height INT,

    -- Niche + enrichment
    niche TEXT,
    ip INET,
    country CHAR(2),
    user_agent TEXT,
    browser TEXT,
    browser_version TEXT,
    os TEXT,
    device_type TEXT
) PARTITION BY RANGE (created_at);

-- Particion default para que los inserts no fallen mientras pg_partman se setea
CREATE TABLE IF NOT EXISTS tracking_events_default PARTITION OF tracking_events DEFAULT;

-- =============================================================================
-- processed_stream_events: idempotency log para el stream_processor
-- =============================================================================
-- Cada DynamoDB Stream record tiene un eventID unico. El stream_processor
-- verifica este eventID antes de insertar en contacts/tracking_events.
-- Sin TTL automatico: la tabla crece con cada evento procesado. Volumen
-- bajo (~200 contacts/mes + ~15k tracking/mes), aceptable en el free tier
-- de Neon. Si crece, hacer un cleanup manual de filas >30 dias.
CREATE TABLE IF NOT EXISTS processed_stream_events (
    event_id TEXT PRIMARY KEY,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    event_type TEXT,  -- 'INSERT' | 'MODIFY' | 'REMOVE'
    table_name TEXT   -- 'contacts' | 'tracking'
);

COMMIT;
