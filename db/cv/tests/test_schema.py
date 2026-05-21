"""@tests test_schema — verifica las invariantes del schema relacional.

Cubre:
- AC-2: ningun texto bilingue vive como columna en su entidad.
- AC-3: el priority por niche vive en `niche_priorities`, NO en las uniones.
- AC-6: el trigger polimorfico rechaza un `entity_id` huerfano.

Corren contra una DB con el schema aplicado (`alembic upgrade head`).
"""

import uuid

import psycopg
import pytest


# Tablas de entidad + el campo bilingue que NO debe estar como columna.
# Si alguna de estas columnas existiera, la migracion a `translations` fallo.
_FORBIDDEN_INLINE_BILINGUAL = [
    ('experiences', 'role_es'),
    ('experiences', 'role_en'),
    ('projects', 'summary_es'),
    ('projects', 'summary_en'),
    ('awards', 'title_es'),
    ('awards', 'motivation_en'),
    ('profile', 'headline_es'),
    ('languages', 'name_en'),
]


@pytest.mark.parametrize(('table', 'column'), _FORBIDDEN_INLINE_BILINGUAL)
def test_no_inline_bilingual_columns(
    conn: psycopg.Connection, table: str, column: str
) -> None:
    """AC-2: ninguna tabla de entidad tiene columnas `*_es`/`*_en`."""
    row = conn.execute(
        """
        SELECT count(*) FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = %s AND column_name = %s
        """,
        (table, column),
    ).fetchone()
    assert row is not None
    assert row[0] == 0


def test_translations_table_has_locale_column(
    conn: psycopg.Connection,
) -> None:
    """AC-2: los textos bilingues viven en `translations`, con `locale`."""
    row = conn.execute(
        """
        SELECT count(*) FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'translations' AND column_name = 'locale'
        """,
    ).fetchone()
    assert row is not None
    assert row[0] == 1


def test_experience_niches_has_no_priority_column(
    conn: psycopg.Connection,
) -> None:
    """AC-3: la union `experience_niches` NO tiene columna `priority`."""
    row = conn.execute(
        """
        SELECT count(*) FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'experience_niches'
          AND column_name = 'priority'
        """,
    ).fetchone()
    assert row is not None
    assert row[0] == 0


def test_niche_priorities_table_exists_with_priority(
    conn: psycopg.Connection,
) -> None:
    """AC-3: el priority por niche vive en `niche_priorities.priority`."""
    row = conn.execute(
        """
        SELECT count(*) FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'niche_priorities'
          AND column_name = 'priority'
        """,
    ).fetchone()
    assert row is not None
    assert row[0] == 1


def test_polymorphic_trigger_rejects_orphan_translation(
    conn: psycopg.Connection,
) -> None:
    """AC-6: insertar una traduccion con `entity_id` inexistente falla."""
    orphan_id = str(uuid.uuid4())
    with (
        pytest.raises(psycopg.errors.RaiseException),
        conn.cursor() as cur,
    ):
        cur.execute(
            """
            INSERT INTO translations
                (entity_type, entity_id, field, locale, value)
            VALUES ('project', %s, 'summary', 'es', 'huerfano')
            """,
            (orphan_id,),
        )
    conn.rollback()


def test_polymorphic_trigger_rejects_orphan_niche_priority(
    conn: psycopg.Connection,
) -> None:
    """AC-6: insertar un niche_priority con `entity_id` huerfano falla."""
    orphan_id = str(uuid.uuid4())
    niche = conn.execute(
        "SELECT id FROM niches WHERE slug = 'generic'"
    ).fetchone()
    assert niche is not None
    with (
        pytest.raises(psycopg.errors.RaiseException),
        conn.cursor() as cur,
    ):
        cur.execute(
            """
            INSERT INTO niche_priorities
                (entity_type, entity_id, niche_id, priority)
            VALUES ('experience', %s, %s, 50)
            """,
            (orphan_id, niche[0]),
        )
    conn.rollback()


def test_enum_types_exist(conn: psycopg.Connection) -> None:
    """Los 7 ENUMs nativos del schema fueron creados."""
    row = conn.execute(
        """
        SELECT count(*) FROM pg_type
        WHERE typtype = 'e' AND typname IN (
            'locale', 'seniority', 'project_type', 'project_status',
            'skill_kind', 'bullet_kind', 'entity_type'
        )
        """,
    ).fetchone()
    assert row is not None
    assert row[0] == 7
