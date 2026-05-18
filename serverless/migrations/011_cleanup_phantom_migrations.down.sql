-- Rollback 011: restaura las filas fantasma en schema_migrations.
--
-- Revierte exactamente el DELETE del forward dejando schema_migrations en
-- el estado previo al 011. ON CONFLICT DO NOTHING por idempotencia.
INSERT INTO schema_migrations (version) VALUES
    ('003_materialized_views'),
    ('004_aggregates_tables')
ON CONFLICT (version) DO NOTHING;
