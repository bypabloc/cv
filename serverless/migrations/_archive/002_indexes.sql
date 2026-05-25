-- Migration 002: indexes
-- Composite + partial + GIN + BRIN segun patrones de query del dashboard.

BEGIN;

-- =============================================================================
-- contacts indexes
-- =============================================================================

-- Lookup por email (CRM filtering, case-insensitive ya por CITEXT)
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts (email);

-- Lookup por created_at (rango temporal: "contactos de la ultima semana")
CREATE INDEX IF NOT EXISTS idx_contacts_created_at ON contacts (created_at DESC);

-- Lookup por niche + created_at (dashboard "contactos por niche este mes")
CREATE INDEX IF NOT EXISTS idx_contacts_niche_created ON contacts (niche, created_at DESC);

-- Lookup por status (CRM: "nuevos por contactar")
CREATE INDEX IF NOT EXISTS idx_contacts_status ON contacts (status)
    WHERE status IN ('new', 'contacted');  -- partial index

-- Full-text search en messages (Spanish dictionary)
CREATE INDEX IF NOT EXISTS idx_contacts_message_fts
    ON contacts USING gin (to_tsvector('spanish', message));

-- =============================================================================
-- tracking_events indexes
-- =============================================================================

-- Session journey: WHERE session_id = X ORDER BY created_at
CREATE INDEX IF NOT EXISTS idx_tracking_session_created
    ON tracking_events (session_id, created_at);

-- BRIN para created_at (gigantes time-series con escritura ordenada)
CREATE INDEX IF NOT EXISTS idx_tracking_created_brin
    ON tracking_events USING brin (created_at);

-- Top landing pages: WHERE page_path = X
CREATE INDEX IF NOT EXISTS idx_tracking_page_path ON tracking_events (page_path);

-- Top referrers: WHERE referrer IS NOT NULL
CREATE INDEX IF NOT EXISTS idx_tracking_referrer ON tracking_events (referrer)
    WHERE referrer IS NOT NULL;  -- partial

-- UTM source breakdown
CREATE INDEX IF NOT EXISTS idx_tracking_utm_source ON tracking_events (utm_source)
    WHERE utm_source IS NOT NULL;

-- Country (geo breakdown)
CREATE INDEX IF NOT EXISTS idx_tracking_country ON tracking_events (country)
    WHERE country IS NOT NULL;

-- Device type breakdown
CREATE INDEX IF NOT EXISTS idx_tracking_device_type ON tracking_events (device_type);

-- Niche + created (dashboard "tracking events por niche")
CREATE INDEX IF NOT EXISTS idx_tracking_niche_created
    ON tracking_events (niche, created_at DESC)
    WHERE niche IS NOT NULL;

COMMIT;
