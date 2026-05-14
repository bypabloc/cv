-- Rollback indexes
BEGIN;
DROP INDEX IF EXISTS idx_contacts_email;
DROP INDEX IF EXISTS idx_contacts_created_at;
DROP INDEX IF EXISTS idx_contacts_niche_created;
DROP INDEX IF EXISTS idx_contacts_status;
DROP INDEX IF EXISTS idx_contacts_message_fts;
DROP INDEX IF EXISTS idx_tracking_session_created;
DROP INDEX IF EXISTS idx_tracking_created_brin;
DROP INDEX IF EXISTS idx_tracking_page_path;
DROP INDEX IF EXISTS idx_tracking_referrer;
DROP INDEX IF EXISTS idx_tracking_utm_source;
DROP INDEX IF EXISTS idx_tracking_country;
DROP INDEX IF EXISTS idx_tracking_device_type;
DROP INDEX IF EXISTS idx_tracking_niche_created;
COMMIT;
