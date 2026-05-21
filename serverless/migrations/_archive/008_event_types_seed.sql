-- Migration 008: seed del catalogo event_types completo (SPEC-200)
-- Amplia el seed de la migration 006 (que solo sembro page_load) con el
-- resto del catalogo: navegacion, clicks, embudo de contacto y engagement.
--
-- Los UUID son literales fijos (UUIDv7), NO uuidv7() en runtime: el frontend
-- los replica como constantes TS en build-time (packages/content). La fuente
-- de verdad de estos literales es SPEC-101 seccion 0.
--
-- page_load (sembrado en 006) NO se re-inserta aqui.
--
-- Idempotente: INSERT ON CONFLICT (id) DO NOTHING. El runner cmd_db_migrate
-- re-aplica todos los .sql, debe poder correr esta migration dos veces.
--
-- Sin BEGIN/COMMIT: el runner migrate.py ya envuelve cada migration en una
-- transaccion (autocommit=False + commit por archivo).

INSERT INTO event_types (id, code_name, description) VALUES
    -- Navegacion
    (
        '019e372b-e0a7-70c6-8e56-2b643ddf1702',
        'spa_navigation',
        'Navegacion client-side entre vistas sin recarga de pagina'
    ),
    -- Clicks
    (
        '019e372b-e0a7-793b-84ed-690388a13b15',
        'cta_click',
        'Click en un call-to-action principal de la pagina'
    ),
    (
        '019e372b-e0a7-776d-8598-81772857f6a8',
        'nav_click',
        'Click en un item de la barra de navegacion'
    ),
    (
        '019e372b-e0a7-7c1b-b8e7-3d822a5ce42d',
        'project_link_click',
        'Click en un enlace de proyecto (demo en vivo o repositorio)'
    ),
    (
        '019e372b-e0a7-7267-8f09-f81f75d90f64',
        'experience_link_click',
        'Click en el enlace externo de una experiencia laboral'
    ),
    (
        '019e372b-e0a7-78a3-ad27-15dfd3d266a2',
        'cv_download',
        'Descarga o apertura del CV del portfolio'
    ),
    (
        '019e372b-e0a7-767c-bbc4-d359c3522e86',
        'theme_toggle',
        'Cambio de tema dark/light/system mediante el toggle'
    ),
    (
        '019e372b-e0a7-7987-8699-8e6381865036',
        'external_link_click',
        'Click en un enlace externo generico fuera del portfolio'
    ),
    -- Embudo de contacto
    (
        '019e372b-e0a7-7f8f-b568-3fbdb8a91756',
        'contact_view',
        'Carga de la pagina de contacto del portfolio'
    ),
    (
        '019e372b-e0a7-7467-a074-603b7e294cf8',
        'contact_form_start',
        'Primer foco en un campo del formulario de contacto'
    ),
    (
        '019e372b-e0a7-7a02-b754-606a5fe38afc',
        'contact_form_submit',
        'Envio del formulario de contacto por el usuario'
    ),
    (
        '019e372b-e0a7-7d1b-9bd3-3cb2ee92b4d7',
        'contact_form_success',
        'Respuesta exitosa del backend al envio del formulario de contacto'
    ),
    (
        '019e372b-e0a7-77f6-897f-17f41a06b2c0',
        'contact_form_error',
        'Respuesta de error del backend al envio del formulario de contacto'
    ),
    -- Engagement
    (
        '019e372b-e0a7-7067-a5c5-d0baf8352385',
        'scroll_depth',
        'Cruce de un umbral de profundidad de scroll (25/50/75/100 %)'
    ),
    (
        '019e372b-e0a7-78dd-a3b5-7cf649c4638f',
        'page_exit',
        'Abandono de la pestana del portfolio (visibilitychange a hidden)'
    )
ON CONFLICT (id) DO NOTHING;
