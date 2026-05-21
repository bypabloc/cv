-- Rollback 009: revierte la columna event_props de tracking_events.
-- Elimina la columna jsonb agregada por el forward (reverso exacto).
--
-- Sin BEGIN/COMMIT: el runner migrate.py ya envuelve el rollback en una
-- transaccion.

ALTER TABLE tracking_events
    DROP COLUMN IF EXISTS event_props;
