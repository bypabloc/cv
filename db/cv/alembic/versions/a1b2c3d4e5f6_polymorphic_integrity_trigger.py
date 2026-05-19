"""polymorphic integrity trigger

Agrega `assert_entity_exists()`: trigger que valida la integridad referencial
de las tablas polimorficas `translations` y `niche_priorities`. Su columna
`entity_id` no puede tener una FK real (apunta a tablas distintas segun
`entity_type`), asi que la integridad se garantiza con este trigger.

Por cada INSERT/UPDATE en esas tablas, el trigger:
1. Resuelve la tabla destino a partir de `NEW.entity_type`.
2. Verifica con un EXISTS dinamico que `NEW.entity_id` existe en esa tabla.
3. Lanza una excepcion si no — la fila huerfana se rechaza.

Revision ID: a1b2c3d4e5f6
Revises: b79eba6beb00
Create Date: 2026-05-18 20:40:00.000000
"""

from collections.abc import Sequence

from alembic import op


revision: str = 'a1b2c3d4e5f6'
down_revision: str | None = 'b79eba6beb00'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Mapa entity_type -> tabla destino. Debe cubrir TODOS los valores del ENUM
# `entity_type` (models/enums.py: EntityType).
_ENTITY_TABLE_MAP = """
      CASE NEW.entity_type
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
      END
"""

_CREATE_FUNCTION = f"""
CREATE OR REPLACE FUNCTION assert_entity_exists()
RETURNS TRIGGER AS $$
DECLARE
    target_table text;
    found boolean;
BEGIN
    target_table := {_ENTITY_TABLE_MAP};
    IF target_table IS NULL THEN
        RAISE EXCEPTION
            'assert_entity_exists: entity_type % no mapeado a ninguna tabla',
            NEW.entity_type;
    END IF;
    EXECUTE format(
        'SELECT EXISTS (SELECT 1 FROM %I WHERE id = $1)', target_table
    ) INTO found USING NEW.entity_id;
    IF NOT found THEN
        RAISE EXCEPTION
            'assert_entity_exists: % % no existe en la tabla %',
            NEW.entity_type, NEW.entity_id, target_table;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

_TRIGGER_TABLES = ('translations', 'niche_priorities')


def upgrade() -> None:
    op.execute(_CREATE_FUNCTION)
    for table in _TRIGGER_TABLES:
        op.execute(f"""
            CREATE TRIGGER trg_{table}_entity_exists
            BEFORE INSERT OR UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION assert_entity_exists();
        """)


def downgrade() -> None:
    for table in _TRIGGER_TABLES:
        op.execute(
            f'DROP TRIGGER IF EXISTS trg_{table}_entity_exists ON {table};'
        )
    op.execute('DROP FUNCTION IF EXISTS assert_entity_exists();')
