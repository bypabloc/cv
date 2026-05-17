-- Migration 006: catalogo event_types
-- Tabla catalogo de tipos de evento de tracking. Fuente de verdad de los
-- UUID; el frontend los replica como constantes TS (packages/content).
--
-- El seed usa UUID literales fijos (NO uuidv7() en runtime) porque el cliente
-- necesita conocer el valor en build-time para replicarlo como constante.
-- Fase 1 siembra solo page_load; SPEC-200 amplia el seed con el resto.
--
-- Idempotente: CREATE TABLE IF NOT EXISTS + INSERT ON CONFLICT DO NOTHING.

BEGIN;

CREATE TABLE IF NOT EXISTS event_types (
    -- UUIDv7 literal fijado en el seed (no uuidv7() de PG: el cliente lo
    -- replica como constante TS en build-time)
    id UUID PRIMARY KEY,
    code_name TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Seed Fase 1: solo page_load. El resto del catalogo lo siembra SPEC-200.
INSERT INTO event_types (id, code_name, description) VALUES
    (
        '019e372b-e0a7-7154-8279-8829bcf6a08c',
        'page_load',
        'Carga inicial de una pagina del portfolio'
    )
ON CONFLICT (id) DO NOTHING;

COMMIT;
