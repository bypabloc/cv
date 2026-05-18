-- Rollback 010: revierte SOLO la columna session_id de contacts.
-- Elimina el indice y la columna session_id (exacto del forward).
--
-- NO toca ip/country/user_agent: son columnas legacy con datos
-- historicos, no fueron creadas por esta migration.

DROP INDEX IF EXISTS idx_contacts_session_id;

ALTER TABLE contacts
    DROP COLUMN IF EXISTS session_id;
