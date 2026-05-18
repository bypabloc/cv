-- Rollback 008: elimina las filas del seed de SPEC-200 de event_types.
-- Borra exactamente los 15 code_name sembrados por el forward; page_load
-- (sembrado en 006) NO se toca. Es el reverso exacto del 008 forward.
--
-- Sin BEGIN/COMMIT: el runner migrate.py ya envuelve el rollback en una
-- transaccion.

DELETE FROM event_types WHERE code_name IN (
    'spa_navigation',
    'cta_click',
    'nav_click',
    'project_link_click',
    'experience_link_click',
    'cv_download',
    'theme_toggle',
    'external_link_click',
    'contact_view',
    'contact_form_start',
    'contact_form_submit',
    'contact_form_success',
    'contact_form_error',
    'scroll_depth',
    'page_exit'
);
