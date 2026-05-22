"""@tests test_seed — verifica el resultado del seed sobre la DB.

Cubre:
- AC-4: los vocabularios (`skills`, `tech_tags`) estan deduplicados.
- AC-5: los conteos por tabla coinciden con la data de los YAML.
- AC-7: el seed es idempotente (re-correrlo deja el mismo estado).

Pre-condicion: el seed ya corrio (`python seed/seed_from_yaml.py`).
"""

import psycopg
import pytest

from seed.seed_from_yaml import run_seed


# Conteos esperados tras el seed — derivados de la data real de los YAML.
_EXPECTED_COUNTS = {
    'profile': 1,
    # profile.niches declara los 5 niches -> 5 filas en profile_niches.
    'profile_niches': 5,
    'experiences': 9,
    'projects': 6,
    'skill_categories': 10,
    'certificates': 11,
    'awards': 2,
    'education': 3,
    'references': 10,
    'languages': 2,
    'publications': 0,
    'niches': 5,
}


@pytest.mark.parametrize(('table', 'expected'), list(_EXPECTED_COUNTS.items()))
def test_seed_row_counts(
    conn: psycopg.Connection, table: str, expected: int
) -> None:
    """AC-5: cada tabla de entidad tiene el numero esperado de filas."""
    row = conn.execute(
        f'SELECT count(*) FROM "{table}"'  # noqa: S608
    ).fetchone()
    assert row is not None
    assert row[0] == expected


def test_skills_vocabulary_deduplicated(
    conn: psycopg.Connection,
) -> None:
    """AC-4: `skills` no tiene nombres duplicados."""
    row = conn.execute(
        'SELECT count(*) - count(DISTINCT name) FROM skills'
    ).fetchone()
    assert row is not None
    assert row[0] == 0


def test_tech_tags_vocabulary_deduplicated(
    conn: psycopg.Connection,
) -> None:
    """AC-4: `tech_tags` no tiene nombres duplicados."""
    row = conn.execute(
        'SELECT count(*) - count(DISTINCT name) FROM tech_tags'
    ).fetchone()
    assert row is not None
    assert row[0] == 0


def test_shared_skill_is_single_row(conn: psycopg.Connection) -> None:
    """AC-4: una skill presente en varios YAML existe como 1 sola fila.

    'TypeScript' aparece en multiples skill_categories y experiences — debe
    haber exactamente una fila en `skills`.
    """
    row = conn.execute(
        "SELECT count(*) FROM skills WHERE name = 'TypeScript'"
    ).fetchone()
    assert row is not None
    assert row[0] == 1


def test_translations_are_bilingual_pairs(
    conn: psycopg.Connection,
) -> None:
    """AC-5: cada (entity, field) traducido tiene exactamente 2 locales."""
    row = conn.execute(
        """
        SELECT count(*) FROM (
            SELECT entity_type, entity_id, field
            FROM translations
            GROUP BY entity_type, entity_id, field
            HAVING count(DISTINCT locale) <> 2
        ) AS incomplete
        """,
    ).fetchone()
    assert row is not None
    assert row[0] == 0


def test_niche_priority_per_pair(conn: psycopg.Connection) -> None:
    """AC-3 + AC-5: una experiencia con priority por niche tiene una fila
    por niche en `niche_priorities`, con el valor correcto.

    `destacame-architect` declara priority en los 5 niches (todos 100).
    """
    rows = conn.execute(
        """
        SELECT n.slug, np.priority
        FROM niche_priorities np
        JOIN experiences e
            ON e.id = np.entity_id AND np.entity_type = 'experience'
        JOIN niches n ON n.id = np.niche_id
        WHERE e.slug = 'destacame-architect'
        ORDER BY n.slug
        """,
    ).fetchall()
    by_niche = dict(rows)
    assert by_niche == {
        'architect': 100,
        'fintech': 100,
        'generic': 100,
        'leader': 100,
        'vibe': 100,
    }


def test_niche_priority_varies_by_niche(
    conn: psycopg.Connection,
) -> None:
    """AC-3: el priority es por (entidad, niche) — distintos niches de la
    misma entidad pueden tener distinto valor.

    `faststruct` (project) declara architect=70, vibe=100, generic=80.
    """
    rows = conn.execute(
        """
        SELECT n.slug, np.priority
        FROM niche_priorities np
        JOIN projects p
            ON p.id = np.entity_id AND np.entity_type = 'project'
        JOIN niches n ON n.id = np.niche_id
        WHERE p.slug = 'faststruct'
        ORDER BY n.slug
        """,
    ).fetchall()
    by_niche = dict(rows)
    assert by_niche == {
        'architect': 70,
        'generic': 80,
        'vibe': 100,
    }


def test_seed_is_idempotent(conn: psycopg.Connection) -> None:
    """AC-7: re-correr el seed deja exactamente los mismos conteos."""
    before = run_seed(conn)
    after = run_seed(conn)
    assert before == after
