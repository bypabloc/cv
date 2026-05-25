"""group tables by domain (cv_/vis_/tax_/i18n_) + normaliza columnas

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-24 21:00:00.000000

Plan group-tables-by-domain — UNA migracion atomica que:

1. Renombra las 37 tablas aplicando prefijo de dominio:
   - cv_*  (28 tablas del CV)
   - vis_* (4 tablas del visitor)
   - tax_* (4 tablas de taxonomy)
   - i18n_* (1 tabla de translations)
2. Renombra la particion default: tracking_events_default -> vis_tracking_events_default
3. Normaliza columnas de fecha (VARCHAR -> DATE):
   - cv_experiences: start_ym/end_ym -> started_on/ended_on
   - cv_awards: awarded_ym -> awarded_on
   - cv_education_entries: start_year/end_year -> started_on/ended_on
4. Agrega slugs UK (kebab-case) + backfill:
   - cv_skills.slug
   - tax_tech_tags.slug
5. Renombra tax_niches.position -> display_order
6. Agrega PK fisica a vis_tracking_events (created_at, visit_id, page_id)
7. Renombra FK columns por cascade del rename de entidad padre:
   - cv_education_entry_niches.education_id -> education_entry_id
   - cv_endorsement_niches.reference_id -> endorsement_id
8. ALTER TYPE entity_type RENAME VALUE 'reference' TO 'endorsement'
9. CREATE OR REPLACE trigger assert_entity_exists() con los nombres
   nuevos de tabla en la lookup

downgrade() revierte cada operacion en orden inverso.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


# Mapa <viejo, nuevo> de renames de tablas (orden importa: padres antes
# de junctions para que las FKs sigan validas).
TABLE_RENAMES: list[tuple[str, str]] = [
    # CV — entidades raiz primero
    ('profile', 'cv_profiles'),
    ('experiences', 'cv_experiences'),
    ('education', 'cv_education_entries'),
    ('projects', 'cv_projects'),
    ('skills', 'cv_skills'),
    ('skill_categories', 'cv_skill_categories'),
    ('awards', 'cv_awards'),
    ('certificates', 'cv_certificates'),
    ('languages', 'cv_languages'),
    ('publications', 'cv_publications'),
    ('references', 'cv_endorsements'),
    # CV — auxiliares 1:N
    ('profile_stats', 'cv_profile_stats'),
    ('experience_bullets', 'cv_experience_bullets'),
    ('project_case_studies', 'cv_project_case_studies'),
    ('project_metrics', 'cv_project_metrics'),
    # CV — junctions
    ('profile_niches', 'cv_profile_niches'),
    ('experience_niches', 'cv_experience_niches'),
    ('experience_skills', 'cv_experience_skills'),
    ('education_niches', 'cv_education_entry_niches'),
    ('project_niches', 'cv_project_niches'),
    ('project_tech_tags', 'cv_project_tech_tags'),
    ('skill_category_skills', 'cv_skill_category_skills'),
    ('skill_category_niches', 'cv_skill_category_niches'),
    ('award_niches', 'cv_award_niches'),
    ('certificate_niches', 'cv_certificate_niches'),
    ('language_niches', 'cv_language_niches'),
    ('publication_niches', 'cv_publication_niches'),
    ('reference_niches', 'cv_endorsement_niches'),
    # Taxonomy
    ('niches', 'tax_niches'),
    ('niche_priorities', 'tax_niche_priorities'),
    ('tech_tags', 'tax_tech_tags'),
    ('event_types', 'tax_event_types'),
    # i18n
    ('translations', 'i18n_translations'),
    # Visitor
    ('sessions', 'vis_sessions'),
    ('session_visits', 'vis_session_visits'),
    ('contacts', 'vis_contacts'),
    ('tracking_events', 'vis_tracking_events'),
]


# Trigger nuevo (post-rename) — reproducido aqui para no depender de
# _init_schema_extras (que puede cambiar en commits futuros sin afectar
# esta migracion historica).
NEW_TRIGGER_FN = """
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

OLD_TRIGGER_FN = """
CREATE OR REPLACE FUNCTION assert_entity_exists()
RETURNS TRIGGER AS $$
DECLARE
    target_table text;
    found boolean;
BEGIN
    target_table := CASE NEW.entity_type
        WHEN 'profile'            THEN 'profile'
        WHEN 'experience'         THEN 'experiences'
        WHEN 'experience_bullet'  THEN 'experience_bullets'
        WHEN 'project'            THEN 'projects'
        WHEN 'project_case_study' THEN 'project_case_studies'
        WHEN 'project_metric'     THEN 'project_metrics'
        WHEN 'skill_category'     THEN 'skill_categories'
        WHEN 'certificate'        THEN 'certificates'
        WHEN 'award'              THEN 'awards'
        WHEN 'education'          THEN 'education'
        WHEN 'reference'          THEN 'references'
        WHEN 'language'           THEN 'languages'
        WHEN 'publication'        THEN 'publications'
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


def upgrade() -> None:
    # 0. Extension unaccent — necesaria para generar slugs ASCII desde
    #    nombres con tildes ('Análisis' -> 'analisis', no 'an-lisis')
    op.execute('CREATE EXTENSION IF NOT EXISTS unaccent')

    # 1. Drop CheckConstraints viejos de fechas. Hay 2 variantes de
    #    nombres segun cuando se aplico la migracion inicial:
    #    - Branches viejas: `ck_<table>_ck_<table>_<field>_format`
    #      (la naming_convention de Alembic prefijo `ck_<table>_` al
    #      nombre del CheckConstraint que ya era `<field>_format`)
    #    - Branches nuevas: `ck_<table>_<field>_format` directo
    #    IF EXISTS cubre ambos casos sin fallar.
    for cname in (
        'ck_experiences_ck_experiences_start_ym_format',
        'ck_experiences_start_ym_format',
    ):
        op.execute(
            f'ALTER TABLE experiences DROP CONSTRAINT IF EXISTS {cname}'
        )
    for cname in (
        'ck_experiences_ck_experiences_end_ym_format',
        'ck_experiences_end_ym_format',
    ):
        op.execute(
            f'ALTER TABLE experiences DROP CONSTRAINT IF EXISTS {cname}'
        )
    for cname in (
        'ck_awards_ck_awards_awarded_ym_format',
        'ck_awards_awarded_ym_format',
    ):
        op.execute(
            f'ALTER TABLE awards DROP CONSTRAINT IF EXISTS {cname}'
        )

    # 2. ALTER COLUMN tipo VARCHAR -> DATE con USING (antes del rename,
    #    para usar los nombres de columna viejos)
    op.execute("""
        ALTER TABLE experiences
        ALTER COLUMN start_ym TYPE date USING (start_ym || '-01')::date
    """)
    op.execute("""
        ALTER TABLE experiences
        ALTER COLUMN end_ym TYPE date USING (
            CASE WHEN end_ym IS NULL THEN NULL
                 ELSE (end_ym || '-01')::date
            END
        )
    """)
    op.execute("""
        ALTER TABLE awards
        ALTER COLUMN awarded_ym TYPE date USING (awarded_ym || '-01')::date
    """)
    # education usa varchar(16): puede contener 'Actual', 'Present', YYYY,
    # YYYY-MM. Convertir robustamente. Strings no-parseables ('Actual',
    # 'Present') -> NULL. end_year era NOT NULL en el schema viejo; aqui
    # se vuelve nullable porque el modelo nuevo lo es (estudios en curso).
    op.execute('ALTER TABLE education ALTER COLUMN end_year DROP NOT NULL')
    op.execute(r"""
        ALTER TABLE education
        ALTER COLUMN start_year TYPE date USING (
            CASE WHEN start_year IS NULL THEN NULL
                 WHEN start_year ~ '^\d{4}-\d{2}-\d{2}$' THEN start_year::date
                 WHEN start_year ~ '^\d{4}-\d{2}$' THEN (start_year || '-01')::date
                 WHEN start_year ~ '^\d{4}$' THEN (start_year || '-01-01')::date
                 ELSE NULL
            END
        )
    """)
    op.execute(r"""
        ALTER TABLE education
        ALTER COLUMN end_year TYPE date USING (
            CASE WHEN end_year IS NULL THEN NULL
                 WHEN end_year ~ '^\d{4}-\d{2}-\d{2}$' THEN end_year::date
                 WHEN end_year ~ '^\d{4}-\d{2}$' THEN (end_year || '-01')::date
                 WHEN end_year ~ '^\d{4}$' THEN (end_year || '-01-01')::date
                 ELSE NULL
            END
        )
    """)

    # 3. Rename columnas de fecha (todavia con nombres de tabla viejos)
    op.alter_column('experiences', 'start_ym', new_column_name='started_on')
    op.alter_column('experiences', 'end_ym', new_column_name='ended_on')
    op.alter_column('awards', 'awarded_ym', new_column_name='awarded_on')
    op.alter_column('education', 'start_year', new_column_name='started_on')
    op.alter_column('education', 'end_year', new_column_name='ended_on')
    # education.end_year era NOT NULL. Lo dejamos asi (ya ended_on DATE NOT NULL).

    # 4. Slugs nuevos en skills y tech_tags. Drop UQ en name, add slug
    #    nullable + backfill + NOT NULL + UQ
    op.drop_constraint('uq_skills_name', 'skills', type_='unique')
    op.add_column('skills', sa.Column('slug', sa.String(120), nullable=True))
    op.execute(
        "UPDATE skills SET slug = trim(both '-' from "
        "regexp_replace(lower(unaccent(name)), '[^a-z0-9]+', '-', 'g'))"
    )
    op.alter_column('skills', 'slug', nullable=False)
    op.create_unique_constraint('uq_skills_slug', 'skills', ['slug'])

    op.drop_constraint('uq_tech_tags_name', 'tech_tags', type_='unique')
    op.add_column('tech_tags', sa.Column('slug', sa.String(120), nullable=True))
    op.execute(
        "UPDATE tech_tags SET slug = trim(both '-' from "
        "regexp_replace(lower(unaccent(name)), '[^a-z0-9]+', '-', 'g'))"
    )
    op.alter_column('tech_tags', 'slug', nullable=False)
    op.create_unique_constraint('uq_tech_tags_slug', 'tech_tags', ['slug'])

    # 5. niches.position -> display_order
    op.alter_column('niches', 'position', new_column_name='display_order')

    # 6. Rename de junction FK columns (antes del rename de las tablas
    #    para minimizar acoplamiento)
    op.alter_column(
        'education_niches', 'education_id',
        new_column_name='education_entry_id',
    )
    op.alter_column(
        'reference_niches', 'reference_id',
        new_column_name='endorsement_id',
    )

    # 7. PRIMARY KEY fisica en tracking_events (antes del rename)
    op.create_primary_key(
        'pk_vis_tracking_events',
        'tracking_events',
        ['created_at', 'visit_id', 'page_id'],
    )

    # 8. ENUM entity_type: 'reference' -> 'endorsement' (PG 10+)
    op.execute("ALTER TYPE entity_type RENAME VALUE 'reference' TO 'endorsement'")

    # 9. Renames de tabla (37). Las FKs internas siguen validas porque PG
    #    actualiza las referencias por OID.
    for old, new in TABLE_RENAMES:
        op.rename_table(old, new)

    # 10. Renombrar la particion default
    op.execute(
        'ALTER TABLE tracking_events_default '
        'RENAME TO vis_tracking_events_default'
    )

    # 11. Trigger con los nombres nuevos
    op.execute(NEW_TRIGGER_FN)


def downgrade() -> None:
    # 1. Restaurar trigger viejo
    op.execute(OLD_TRIGGER_FN)

    # 2. Particion default
    op.execute(
        'ALTER TABLE vis_tracking_events_default '
        'RENAME TO tracking_events_default'
    )

    # 3. Renames de tabla en reverso
    for new, old in reversed([(o, n) for o, n in TABLE_RENAMES]):
        op.rename_table(old, new)

    # 4. ENUM entity_type rename back
    op.execute("ALTER TYPE entity_type RENAME VALUE 'endorsement' TO 'reference'")

    # 5. Drop PK fisica de tracking_events
    op.drop_constraint(
        'pk_vis_tracking_events', 'tracking_events', type_='primary',
    )

    # 6. Rename de junction FK columns reverso
    op.alter_column(
        'reference_niches', 'endorsement_id',
        new_column_name='reference_id',
    )
    op.alter_column(
        'education_niches', 'education_entry_id',
        new_column_name='education_id',
    )

    # 7. niches.display_order -> position
    op.alter_column('niches', 'display_order', new_column_name='position')

    # 8. Drop slugs y restaurar UQ en name
    op.drop_constraint('uq_tech_tags_slug', 'tech_tags', type_='unique')
    op.drop_column('tech_tags', 'slug')
    op.create_unique_constraint('uq_tech_tags_name', 'tech_tags', ['name'])

    op.drop_constraint('uq_skills_slug', 'skills', type_='unique')
    op.drop_column('skills', 'slug')
    op.create_unique_constraint('uq_skills_name', 'skills', ['name'])

    # 9. Rename columnas de fecha reverso
    op.alter_column('education', 'ended_on', new_column_name='end_year')
    op.alter_column('education', 'started_on', new_column_name='start_year')
    op.alter_column('awards', 'awarded_on', new_column_name='awarded_ym')
    op.alter_column('experiences', 'ended_on', new_column_name='end_ym')
    op.alter_column('experiences', 'started_on', new_column_name='start_ym')

    # 10. ALTER COLUMN DATE -> VARCHAR (perderia el dia exacto pero el
    #     schema viejo solo tenia precision YYYY-MM)
    op.execute("""
        ALTER TABLE experiences
        ALTER COLUMN start_ym TYPE varchar(7) USING to_char(start_ym, 'YYYY-MM')
    """)
    op.execute("""
        ALTER TABLE experiences
        ALTER COLUMN end_ym TYPE varchar(7) USING (
            CASE WHEN end_ym IS NULL THEN NULL
                 ELSE to_char(end_ym, 'YYYY-MM')
            END
        )
    """)
    op.execute("""
        ALTER TABLE awards
        ALTER COLUMN awarded_ym TYPE varchar(7) USING to_char(awarded_ym, 'YYYY-MM')
    """)
    op.execute("""
        ALTER TABLE education
        ALTER COLUMN start_year TYPE varchar(16) USING to_char(start_year, 'YYYY-MM-DD')
    """)
    op.execute("""
        ALTER TABLE education
        ALTER COLUMN end_year TYPE varchar(16) USING (
            CASE WHEN end_year IS NULL THEN NULL
                 ELSE to_char(end_year, 'YYYY-MM-DD')
            END
        )
    """)

    # 11. Re-crear CheckConstraints viejos de formato YYYY-MM. Usamos
    #     op.execute directo para preservar los nombres exactos del schema
    #     original (con el prefijo `ck_<table>_` doble por la naming
    #     convention de Alembic).
    op.execute(
        r"ALTER TABLE experiences ADD CONSTRAINT "
        r"ck_experiences_ck_experiences_start_ym_format "
        r"CHECK (start_ym ~ '^\d{4}-(0[1-9]|1[0-2])$')"
    )
    op.execute(
        r"ALTER TABLE experiences ADD CONSTRAINT "
        r"ck_experiences_ck_experiences_end_ym_format "
        r"CHECK (end_ym IS NULL OR end_ym ~ '^\d{4}-(0[1-9]|1[0-2])$')"
    )
    op.execute(
        r"ALTER TABLE awards ADD CONSTRAINT "
        r"ck_awards_ck_awards_awarded_ym_format "
        r"CHECK (awarded_ym ~ '^\d{4}-(0[1-9]|1[0-2])$')"
    )
