-- Migration 009: columna event_props jsonb en tracking_events (SPEC-200)
-- Almacena datos especificos por tipo de evento (href del link clickeado,
-- profundidad de scroll, campo del formulario, codigo de error, etc.).
--
-- event_props: JSONB nullable. Un solo campo flexible evita una columna por
-- atributo y mantiene el schema estable al agregar tipos de evento nuevos.
--
-- tracking_events esta particionada por RANGE(created_at): el ALTER TABLE
-- sobre la tabla padre propaga a todas las particiones.
--
-- Idempotente: ADD COLUMN IF NOT EXISTS. El runner cmd_db_migrate re-aplica
-- todos los .sql, debe poder correr esta migration dos veces.
--
-- Sin BEGIN/COMMIT: el runner migrate.py ya envuelve cada migration en una
-- transaccion (autocommit=False + commit por archivo).

ALTER TABLE tracking_events
    ADD COLUMN IF NOT EXISTS event_props JSONB;
