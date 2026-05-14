-- Migration 003: materialized views
-- MVs precomputadas + refresh nightly por aggregator.
-- CONCURRENTLY no bloquea reads en refresh.

BEGIN;

-- =============================================================================
-- mv_contacts_by_month_niche: contacts agrupados por mes + niche
-- =============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_contacts_by_month_niche AS
SELECT
    DATE_TRUNC('month', created_at) AS month,
    COALESCE(niche, 'unknown') AS niche,
    COUNT(*) AS contact_count,
    COUNT(*) FILTER (WHERE status = 'converted') AS converted_count
FROM contacts
GROUP BY 1, 2
ORDER BY 1 DESC, 2;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_contacts_month_niche
    ON mv_contacts_by_month_niche (month, niche);

-- =============================================================================
-- mv_top_landing_pages: top 100 paginas por visitas (ultimos 30 dias)
-- =============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_top_landing_pages AS
SELECT
    page_path,
    COUNT(*) AS visit_count,
    COUNT(DISTINCT session_id) AS unique_sessions,
    COUNT(*) FILTER (WHERE country IS NOT NULL) AS visits_with_country
FROM tracking_events
WHERE created_at >= NOW() - INTERVAL '30 days'
    AND page_path IS NOT NULL
GROUP BY page_path
ORDER BY visit_count DESC
LIMIT 100;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_top_landing_path
    ON mv_top_landing_pages (page_path);

-- =============================================================================
-- mv_session_journey: paginas por sesion en orden temporal (LAG/LEAD)
-- =============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_session_journey AS
SELECT
    session_id,
    page_id,
    page_path,
    created_at,
    LAG(page_path) OVER (PARTITION BY session_id ORDER BY created_at) AS prev_page,
    LEAD(page_path) OVER (PARTITION BY session_id ORDER BY created_at) AS next_page,
    ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY created_at) AS step_in_session
FROM tracking_events
WHERE created_at >= NOW() - INTERVAL '30 days';

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_session_journey
    ON mv_session_journey (session_id, page_id);

COMMIT;
