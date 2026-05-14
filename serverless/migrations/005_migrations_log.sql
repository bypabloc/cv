-- Migration 005: log de migraciones aplicadas
-- Tabla para tracking de migrations corridas (pattern goose/sqlx/flyway)

BEGIN;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    checksum TEXT,
    duration_ms INT
);

-- Auto-registrar las migrations corridas (idempotente: ON CONFLICT DO NOTHING)
INSERT INTO schema_migrations (version) VALUES
    ('001_init_schema'),
    ('002_indexes'),
    ('003_materialized_views'),
    ('004_aggregates_tables'),
    ('005_migrations_log')
ON CONFLICT (version) DO NOTHING;

COMMIT;
