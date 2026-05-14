-- Migration 004: daily_metrics + tracking_daily_aggregates
-- Tablas precomputadas que el aggregator Lambda popula cada noche.

BEGIN;

-- =============================================================================
-- daily_metrics: KPIs del dashboard (1 row por dia)
-- =============================================================================
CREATE TABLE IF NOT EXISTS daily_metrics (
    metric_date DATE PRIMARY KEY,

    -- Volume
    total_contacts INT NOT NULL DEFAULT 0,
    total_tracking_events INT NOT NULL DEFAULT 0,
    unique_sessions INT NOT NULL DEFAULT 0,

    -- Conversion
    new_contacts INT NOT NULL DEFAULT 0,
    converted_contacts INT NOT NULL DEFAULT 0,
    conversion_rate NUMERIC(5, 4) DEFAULT 0,  -- 0.0000 a 1.0000

    -- Top breakdowns (JSON para flexibilidad)
    contacts_by_niche JSONB,
    contacts_by_service_type JSONB,
    tracking_by_device JSONB,
    tracking_by_country JSONB,

    -- Computed_at
    computed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_metrics (metric_date DESC);

-- =============================================================================
-- tracking_daily_aggregates: pre-agrupado por dia + niche + device
-- =============================================================================
CREATE TABLE IF NOT EXISTS tracking_daily_aggregates (
    metric_date DATE NOT NULL,
    niche TEXT NOT NULL DEFAULT 'unknown',
    device_type TEXT NOT NULL DEFAULT 'unknown',

    event_count INT NOT NULL DEFAULT 0,
    unique_sessions INT NOT NULL DEFAULT 0,
    countries JSONB,  -- {"US": 12, "MX": 5, ...}
    top_pages JSONB,  -- [{"page_path": "/projects", "count": 10}, ...]

    computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (metric_date, niche, device_type)
);

CREATE INDEX IF NOT EXISTS idx_tracking_daily_date_niche
    ON tracking_daily_aggregates (metric_date DESC, niche);

COMMIT;
