-- Rollback 007: revierte las columnas event_id/event_type_id de tracking_events.
-- Elimina el constraint, el indice y las dos columnas (exacto del forward).

BEGIN;

DROP INDEX IF EXISTS idx_tracking_event_type;

ALTER TABLE tracking_events
    DROP CONSTRAINT IF EXISTS fk_tracking_events_event_type;

ALTER TABLE tracking_events
    DROP COLUMN IF EXISTS event_id,
    DROP COLUMN IF EXISTS event_type_id;

COMMIT;
