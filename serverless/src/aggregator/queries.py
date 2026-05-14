"""SQL queries del aggregator. Constants para mantener sintaxis legible."""

from __future__ import annotations

# Compute daily_metrics para el dia anterior (ayer en UTC).
COMPUTE_DAILY_METRICS = """
INSERT INTO daily_metrics (
    metric_date,
    total_contacts,
    total_tracking_events,
    unique_sessions,
    new_contacts,
    converted_contacts,
    conversion_rate,
    contacts_by_niche,
    contacts_by_service_type,
    tracking_by_device,
    tracking_by_country
)
SELECT
    %(target_date)s::date,
    -- Contacts del dia
    (SELECT COUNT(*) FROM contacts
     WHERE created_at::date = %(target_date)s::date),
    -- Tracking events del dia
    (SELECT COUNT(*) FROM tracking_events
     WHERE created_at::date = %(target_date)s::date),
    -- Unique sessions del dia
    (SELECT COUNT(DISTINCT session_id) FROM tracking_events
     WHERE created_at::date = %(target_date)s::date),
    -- new_contacts (status='new')
    (SELECT COUNT(*) FROM contacts
     WHERE created_at::date = %(target_date)s::date AND status = 'new'),
    -- converted_contacts (status='converted')
    (SELECT COUNT(*) FROM contacts
     WHERE created_at::date = %(target_date)s::date AND status = 'converted'),
    -- conversion_rate
    COALESCE(
        (SELECT COUNT(*) FILTER (WHERE status = 'converted')::numeric
         / NULLIF(COUNT(*), 0)
         FROM contacts WHERE created_at::date = %(target_date)s::date),
        0
    ),
    -- contacts_by_niche JSONB
    COALESCE(
        (SELECT jsonb_object_agg(COALESCE(niche, 'unknown'), cnt)
         FROM (SELECT niche, COUNT(*) AS cnt FROM contacts
               WHERE created_at::date = %(target_date)s::date
               GROUP BY niche) q),
        '{}'::jsonb
    ),
    -- contacts_by_service_type
    COALESCE(
        (SELECT jsonb_object_agg(COALESCE(service_type, 'unknown'), cnt)
         FROM (SELECT service_type, COUNT(*) AS cnt FROM contacts
               WHERE created_at::date = %(target_date)s::date
               GROUP BY service_type) q),
        '{}'::jsonb
    ),
    -- tracking_by_device
    COALESCE(
        (SELECT jsonb_object_agg(COALESCE(device_type, 'unknown'), cnt)
         FROM (SELECT device_type, COUNT(*) AS cnt FROM tracking_events
               WHERE created_at::date = %(target_date)s::date
               GROUP BY device_type) q),
        '{}'::jsonb
    ),
    -- tracking_by_country
    COALESCE(
        (SELECT jsonb_object_agg(COALESCE(country, 'unknown'), cnt)
         FROM (SELECT country, COUNT(*) AS cnt FROM tracking_events
               WHERE created_at::date = %(target_date)s::date
               GROUP BY country) q),
        '{}'::jsonb
    )
ON CONFLICT (metric_date) DO UPDATE SET
    total_contacts = EXCLUDED.total_contacts,
    total_tracking_events = EXCLUDED.total_tracking_events,
    unique_sessions = EXCLUDED.unique_sessions,
    new_contacts = EXCLUDED.new_contacts,
    converted_contacts = EXCLUDED.converted_contacts,
    conversion_rate = EXCLUDED.conversion_rate,
    contacts_by_niche = EXCLUDED.contacts_by_niche,
    contacts_by_service_type = EXCLUDED.contacts_by_service_type,
    tracking_by_device = EXCLUDED.tracking_by_device,
    tracking_by_country = EXCLUDED.tracking_by_country,
    computed_at = now();
"""

# Refresh MVs (CONCURRENTLY no bloquea reads)
REFRESH_MV_CONTACTS = 'REFRESH MATERIALIZED VIEW CONCURRENTLY mv_contacts_by_month_niche'
REFRESH_MV_LANDING = 'REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_landing_pages'
REFRESH_MV_JOURNEY = 'REFRESH MATERIALIZED VIEW CONCURRENTLY mv_session_journey'

# Cleanup processed_stream_events > 30 dias (anti-bloat)
CLEANUP_OLD_EVENTS = """
DELETE FROM processed_stream_events
WHERE processed_at < NOW() - INTERVAL '30 days'
"""
