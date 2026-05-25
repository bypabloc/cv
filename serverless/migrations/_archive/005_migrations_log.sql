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
-- Las migrations 003/004 nunca existieron (servian al dashboard descartado);
-- se quitan de este INSERT. Para los stages donde el 005 ya corrio con esas
-- filas, la migration 008 las borra (ver SPEC-204).
INSERT INTO schema_migrations (version) VALUES
    ('001_init_schema'),
    ('002_indexes'),
    ('005_migrations_log')
ON CONFLICT (version) DO NOTHING;

COMMIT;
