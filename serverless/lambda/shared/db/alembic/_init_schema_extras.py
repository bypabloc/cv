"""@module _init_schema_extras — piezas de la migracion inicial que Alembic
no autogenera.

La migracion inicial (`*_init_unified_schema.py`) las importa. Viven aparte
para que, si la migracion se regenera con `--autogenerate`, baste re-aplicar
las llamadas a estas constantes/funciones (no re-pegar ~200 lineas).

Contiene:
- `create_citext_extension` / `create_partition_default` — DDL que Alembic
  no detecta (extension, particion).
- `entity_trigger_fn_sql` + `entity_trigger_tables` — trigger de integridad
  polimorfica de `translations` / `niche_priorities`.
- `event_types_seed` — los 16 tipos del catalogo (UUIDv7 literales).
- `enum_type_names` — los ENUMs nativos a dropear en el downgrade.
"""


# DDL que el autogenerate de Alembic no detecta.
def create_citext_extension() -> str:
    """SQL: la extension citext (la columna `contacts.email` la usa)."""
    return 'CREATE EXTENSION IF NOT EXISTS citext'


def create_partition_default() -> str:
    """SQL: la particion default de `vis_tracking_events`. Sin ella, un INSERT
    cuya `created_at` no cae en ninguna particion explicita falla.
    """
    return (
        'CREATE TABLE IF NOT EXISTS vis_tracking_events_default '
        'PARTITION OF vis_tracking_events DEFAULT'
    )


# Trigger de integridad polimorfica: valida el `entity_id` de translations /
# niche_priorities (apunta a tablas distintas segun `entity_type`, no puede
# ser FK real).
entity_trigger_fn_sql = """
CREATE OR REPLACE FUNCTION assert_entity_exists()
RETURNS TRIGGER AS $$
DECLARE
    target_table text;
    found boolean;
BEGIN
    target_table := CASE NEW.entity_type
        WHEN 'profile'            THEN 'cv_profiles'
        WHEN 'experience'         THEN 'cv_experiences'
        WHEN 'experience_bullet'  THEN 'cv_experience_bullets'
        WHEN 'project'            THEN 'cv_projects'
        WHEN 'project_case_study' THEN 'cv_project_case_studies'
        WHEN 'project_metric'     THEN 'cv_project_metrics'
        WHEN 'skill_category'     THEN 'cv_skill_categories'
        WHEN 'certificate'        THEN 'cv_certificates'
        WHEN 'award'              THEN 'cv_awards'
        WHEN 'education'          THEN 'cv_education_entries'
        WHEN 'endorsement'        THEN 'cv_endorsements'
        WHEN 'language'           THEN 'cv_languages'
        WHEN 'publication'        THEN 'cv_publications'
    END;
    IF target_table IS NULL THEN
        RAISE EXCEPTION
            'assert_entity_exists: entity_type % no mapeado', NEW.entity_type;
    END IF;
    EXECUTE format(
        'SELECT EXISTS (SELECT 1 FROM %I WHERE id = $1)', target_table
    ) INTO found USING NEW.entity_id;
    IF NOT found THEN
        RAISE EXCEPTION
            'assert_entity_exists: % % no existe en %',
            NEW.entity_type, NEW.entity_id, target_table;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

# Tablas polimorficas a las que se les engancha el trigger (post-rename).
entity_trigger_tables = ('i18n_translations', 'tax_niche_priorities')

# ENUMs nativos creados por el autogenerate — Alembic no los dropea en el
# downgrade, hay que hacerlo explicito.
enum_type_names = (
    'locale',
    'seniority',
    'project_type',
    'project_status',
    'skill_kind',
    'bullet_kind',
    'entity_type',
)

# Seed del catalogo event_types (migraciones 006 + 008). UUIDv7 literales:
# el frontend los replica como constantes TS en build-time.
event_types_seed = [
    {
        'id': '019e372b-e0a7-7154-8279-8829bcf6a08c',
        'code_name': 'page_load',
        'description': 'Carga inicial de una pagina del portfolio',
    },
    {
        'id': '019e372b-e0a7-70c6-8e56-2b643ddf1702',
        'code_name': 'spa_navigation',
        'description': (
            'Navegacion client-side entre vistas sin recarga de pagina'
        ),
    },
    {
        'id': '019e372b-e0a7-793b-84ed-690388a13b15',
        'code_name': 'cta_click',
        'description': 'Click en un call-to-action principal de la pagina',
    },
    {
        'id': '019e372b-e0a7-776d-8598-81772857f6a8',
        'code_name': 'nav_click',
        'description': 'Click en un item de la barra de navegacion',
    },
    {
        'id': '019e372b-e0a7-7c1b-b8e7-3d822a5ce42d',
        'code_name': 'project_link_click',
        'description': (
            'Click en un enlace de proyecto (demo en vivo o repositorio)'
        ),
    },
    {
        'id': '019e372b-e0a7-7267-8f09-f81f75d90f64',
        'code_name': 'experience_link_click',
        'description': (
            'Click en el enlace externo de una experiencia laboral'
        ),
    },
    {
        'id': '019e372b-e0a7-78a3-ad27-15dfd3d266a2',
        'code_name': 'cv_download',
        'description': 'Descarga o apertura del CV del portfolio',
    },
    {
        'id': '019e372b-e0a7-767c-bbc4-d359c3522e86',
        'code_name': 'theme_toggle',
        'description': (
            'Cambio de tema dark/light/system mediante el toggle'
        ),
    },
    {
        'id': '019e372b-e0a7-7987-8699-8e6381865036',
        'code_name': 'external_link_click',
        'description': (
            'Click en un enlace externo generico fuera del portfolio'
        ),
    },
    {
        'id': '019e372b-e0a7-7f8f-b568-3fbdb8a91756',
        'code_name': 'contact_view',
        'description': 'Carga de la pagina de contacto del portfolio',
    },
    {
        'id': '019e372b-e0a7-7467-a074-603b7e294cf8',
        'code_name': 'contact_form_start',
        'description': 'Primer foco en un campo del formulario de contacto',
    },
    {
        'id': '019e372b-e0a7-7a02-b754-606a5fe38afc',
        'code_name': 'contact_form_submit',
        'description': 'Envio del formulario de contacto por el usuario',
    },
    {
        'id': '019e372b-e0a7-7d1b-9bd3-3cb2ee92b4d7',
        'code_name': 'contact_form_success',
        'description': (
            'Respuesta exitosa del backend al envio del formulario de '
            'contacto'
        ),
    },
    {
        'id': '019e372b-e0a7-77f6-897f-17f41a06b2c0',
        'code_name': 'contact_form_error',
        'description': (
            'Respuesta de error del backend al envio del formulario de '
            'contacto'
        ),
    },
    {
        'id': '019e372b-e0a7-7067-a5c5-d0baf8352385',
        'code_name': 'scroll_depth',
        'description': (
            'Cruce de un umbral de profundidad de scroll (25/50/75/100 %)'
        ),
    },
    {
        'id': '019e372b-e0a7-78dd-a3b5-7cf649c4638f',
        'code_name': 'page_exit',
        'description': (
            'Abandono de la pestana del portfolio (visibilitychange a '
            'hidden)'
        ),
    },
]
