-- Migration 007: columnas event_id + event_type_id en tracking_events
-- Enlaza cada evento de tracking con su tipo en el catalogo event_types.
--
-- event_id    : UUID del evento generado por el cliente (idempotencia en
--               reintentos de sendBeacon). NO es FK.
-- event_type_id: FK al catalogo event_types(id).
--
-- tracking_events esta particionada por RANGE(created_at): el ALTER TABLE
-- sobre la tabla padre propaga a todas las particiones. PG soporta FK en
-- tablas particionadas (PG12+).
--
-- Idempotente: ADD COLUMN IF NOT EXISTS + CREATE INDEX IF NOT EXISTS. El
-- ADD CONSTRAINT no soporta IF NOT EXISTS en PG, asi que va dentro de un
-- bloque DO que verifica pg_constraint primero (el runner cmd_db_migrate
-- re-aplica todos los .sql, debe poder correr esta migration dos veces).

BEGIN;

ALTER TABLE tracking_events
    ADD COLUMN IF NOT EXISTS event_id UUID,
    ADD COLUMN IF NOT EXISTS event_type_id UUID;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_tracking_events_event_type'
    ) THEN
        ALTER TABLE tracking_events
            ADD CONSTRAINT fk_tracking_events_event_type
            FOREIGN KEY (event_type_id) REFERENCES event_types (id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_tracking_event_type
    ON tracking_events (event_type_id);

COMMIT;
