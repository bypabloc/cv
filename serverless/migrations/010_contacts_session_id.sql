-- Migration 010: columna session_id en contacts
-- Enlaza cada contacto con su sesion de tracking (cf_session) para
-- correlacionar con tracking_events sin duplicar ip/country/user_agent.
--
-- session_id : identificador de sesion del visitante (20-64 chars),
--              misma key cf_session que emite el TrackingPixel. NO es FK:
--              tracking_events tiene TTL de 60 dias y un contacto puede
--              sobrevivir a sus eventos -> correlacion logica via JOIN.
--
-- Las columnas legacy ip/country/user_agent NO se tocan: conservan los
-- datos historicos ya capturados. Los contactos nuevos las dejan en NULL
-- (el stream_processor deja de poblarlas).
--
-- El runner cmd_db_migrate re-aplica todos los .sql, debe poder correr
-- esta migration dos veces -> ADD COLUMN IF NOT EXISTS + CREATE INDEX
-- IF NOT EXISTS. El runner ya envuelve cada migration en una transaccion.

ALTER TABLE contacts
    ADD COLUMN IF NOT EXISTS session_id TEXT;

-- Correlacion: WHERE session_id = X (JOIN con tracking_events).
CREATE INDEX IF NOT EXISTS idx_contacts_session_id
    ON contacts (session_id)
    WHERE session_id IS NOT NULL;
