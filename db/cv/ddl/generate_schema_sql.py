"""@script generate_schema_sql — emite el DDL plano del schema del CV.

Genera `db/cv/ddl/schema.sql` a partir de los modelos SQLAlchemy
(`models.Base.metadata`) usando un mock engine del dialecto PostgreSQL —
sin conectar a ninguna DB y sin depender de `pg_dump` (que exige una
version cliente >= servidor).

El DDL plano es material de REFERENCIA / documentacion. La fuente de verdad
del schema son las migraciones Alembic; este archivo facilita leer el
schema completo sin Python ni una DB. Incluye, en orden:
  1. Los `CREATE TYPE ... AS ENUM`.
  2. Los `CREATE TABLE` (con PK, FK, CHECK, UNIQUE).
  3. La funcion + triggers de integridad polimorfica.

Uso:
    python ddl/generate_schema_sql.py
"""

from pathlib import Path
import sys


# El script vive en db/cv/ddl/; los modelos en db/cv/. Agrega db/cv al path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_mock_engine
from sqlalchemy.schema import CreateTable

from models import Base
from models.enums import bullet_kind_enum
from models.enums import entity_type_enum
from models.enums import locale_enum
from models.enums import project_status_enum
from models.enums import project_type_enum
from models.enums import seniority_enum
from models.enums import skill_kind_enum


_ENUMS = (
    locale_enum,
    seniority_enum,
    project_type_enum,
    project_status_enum,
    skill_kind_enum,
    bullet_kind_enum,
    entity_type_enum,
)

_HEADER = """\
-- ===========================================================================
-- Schema relacional del CV — DDL de referencia (PostgreSQL 18)
-- ===========================================================================
-- GENERADO por db/cv/ddl/generate_schema_sql.py — NO editar a mano.
-- La fuente de verdad del schema son las migraciones Alembic
-- (db/cv/alembic/versions/). Este archivo es solo documentacion legible.
-- ===========================================================================

SET search_path TO public;
"""

_TRIGGER_SQL = """\

-- ---------------------------------------------------------------------------
-- Integridad polimorfica de translations / niche_priorities.
-- `entity_id` apunta a tablas distintas segun `entity_type`, asi que no
-- puede tener una FK real — este trigger la valida en cada INSERT/UPDATE.
-- ---------------------------------------------------------------------------
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

CREATE TRIGGER trg_translations_entity_exists
    BEFORE INSERT OR UPDATE ON translations
    FOR EACH ROW EXECUTE FUNCTION assert_entity_exists();

CREATE TRIGGER trg_niche_priorities_entity_exists
    BEFORE INSERT OR UPDATE ON niche_priorities
    FOR EACH ROW EXECUTE FUNCTION assert_entity_exists();
"""


def main() -> None:
    statements: list[str] = []
    engine = create_mock_engine(
        'postgresql+psycopg://',
        lambda sql, *_a, **_k: statements.append(
            str(sql.compile(dialect=engine.dialect)).strip()
        ),
    )

    out = [_HEADER]

    # 1. ENUMs nativos.
    out.append('-- Tipos ENUM nativos.')
    for enum in _ENUMS:
        values = ', '.join(f"'{v}'" for v in enum.enums)
        out.append(f'CREATE TYPE {enum.name} AS ENUM ({values});')
    out.append('')

    # 2. CREATE TABLE en orden de dependencia (metadata.sorted_tables).
    out.append('-- Tablas.')
    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=engine.dialect))
        out.append(ddl.strip() + ';')
        out.append('')

    # 3. Trigger de integridad polimorfica.
    out.append(_TRIGGER_SQL)

    target = Path(__file__).parent / 'schema.sql'
    target.write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(f'schema.sql generado: {target} ({len(out)} bloques)')


if __name__ == '__main__':
    main()
