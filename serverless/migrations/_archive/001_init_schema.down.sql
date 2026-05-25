-- Rollback de 001_init_schema.sql
BEGIN;
DROP TABLE IF EXISTS processed_stream_events CASCADE;
DROP TABLE IF EXISTS tracking_events CASCADE;
DROP TABLE IF EXISTS contacts CASCADE;
COMMIT;
