"""@script seed_from_yaml — carga la data del CV (YAML) en PostgreSQL.

Lee los YAML de `packages/content/src/data/` y los inserta en el schema
relacional del CV. Es IDEMPOTENTE: cada fila se inserta con `ON CONFLICT`
sobre su clave natural (`slug` / clave compuesta), asi que correr el seed
N veces deja siempre el mismo estado.

Requisitos:
- El schema debe estar creado (`alembic upgrade head`).
- `CV_DATABASE_URL` exportada (ver seed/db_url.py).

Uso:
    CV_DATABASE_URL="$(...)" python seed/seed_from_yaml.py

Estrategia:
1. Vocabularios deduplicados (`niches`, `skills`, `tech_tags`) primero.
2. Entidades (profile, experiences, projects, ...) — UUID resuelto por slug.
3. Estructuras hijas (bullets, case studies, metrics) y uniones N:M.
4. Traducciones polimorficas + niche_priorities al final (el trigger exige
   que la entidad ya exista).
"""

from pathlib import Path
import sys
from typing import Any

import psycopg
import yaml


# Import robusto de `db_url`: funciona tanto al ejecutar el script directo
# (`python seed/seed_from_yaml.py`, cwd=db/cv) como al importarlo como
# paquete desde los tests (`from seed.seed_from_yaml import ...`).
try:
    from seed.db_url import get_database_url
except ImportError:
    from db_url import get_database_url


# packages/content/src/data — fuente de los YAML del CV.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DATA_DIR = _REPO_ROOT / 'packages' / 'content' / 'src' / 'data'

# Los 5 niches del portfolio, en orden canonico de presentacion.
_NICHES = ['fintech', 'architect', 'leader', 'vibe', 'generic']


# ---------------------------------------------------------------------------
# Carga de YAML
# ---------------------------------------------------------------------------


def _load_dir(entity: str) -> list[tuple[str, dict[str, Any]]]:
    """Carga todos los YAML de `data/<entity>/`, ordenados por filename.

    Retorna `(slug, data)` por archivo. El slug se deriva del filename
    (igual que el frontend) cuando el YAML no lo declara.
    """
    folder = _DATA_DIR / entity
    if not folder.is_dir():
        return []
    out: list[tuple[str, dict[str, Any]]] = []
    for path in sorted(folder.glob('*.yaml')):
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
        if data is None:
            continue
        slug = data.get('slug', path.stem)
        out.append((slug, data))
    return out


def _load_profile() -> dict[str, Any]:
    """Extrae el dict del profile del archivo TS `data/profile.ts`.

    `profile.ts` no es YAML; el objeto vive dentro de `ProfileSchema.parse(
    {...})`. Se parsea el bloque entre llaves como YAML laxo — funciona
    porque el objeto usa sintaxis compatible (claves, strings, listas).
    """
    raw = (_DATA_DIR / 'profile.ts').read_text(encoding='utf-8')
    start = raw.index('ProfileSchema.parse(') + len('ProfileSchema.parse(')
    depth = 0
    end = start
    for i in range(start, len(raw)):
        if raw[i] == '{':
            depth += 1
        elif raw[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    block = raw[start:end]
    # TS -> YAML laxo: quita comas finales y comillas de claves no son
    # necesarias. yaml.safe_load tolera el objeto tal cual (claves sin
    # comillas, strings con comillas simples/dobles).
    return yaml.safe_load(block)


# ---------------------------------------------------------------------------
# Helpers de insercion idempotente
# ---------------------------------------------------------------------------


def _require_id(cur: psycopg.Cursor) -> str:
    """Devuelve el `id` del `RETURNING id` recien ejecutado.

    Toda sentencia que lo invoca usa `RETURNING id`, asi que siempre hay
    fila; si no la hubiera, es un bug del seed — falla explicito.
    """
    row = cur.fetchone()
    if row is None:
        raise RuntimeError('INSERT ... RETURNING id no devolvio fila')
    return row[0]


def _upsert_returning_id(
    cur: psycopg.Cursor,
    table: str,
    natural_key: str,
    columns: dict[str, Any],
) -> str:
    """Inserta una fila y devuelve su `id`. Idempotente sobre `natural_key`.

    Si la fila ya existe (mismo valor de `natural_key`), no la modifica y
    devuelve el `id` existente — el seed se puede correr N veces.

    El nombre de tabla se cita con comillas dobles: `references` es una
    palabra reservada de SQL y sin comillas el INSERT falla.
    """
    cols = list(columns.keys())
    placeholders = ', '.join(['%s'] * len(cols))
    col_list = ', '.join(cols)
    # S608: `table`/`col_list`/`natural_key` provienen de constantes internas
    # del seed (nombres de tabla/columna del propio schema), NUNCA de input
    # externo. No hay vector de inyeccion. Los VALUES si van parametrizados.
    query = f"""
        INSERT INTO "{table}" ({col_list})
        VALUES ({placeholders})
        ON CONFLICT ({natural_key}) DO UPDATE
            SET {natural_key} = EXCLUDED.{natural_key}
        RETURNING id
        """  # noqa: S608
    cur.execute(query, list(columns.values()))
    return _require_id(cur)


def _set_translation(
    cur: psycopg.Cursor,
    entity_type: str,
    entity_id: str,
    field: str,
    bilang: dict[str, str] | None,
) -> None:
    """Inserta (o actualiza) las 2 filas es/en de un campo bilingue.

    `bilang` es el dict `{es, en}` del YAML. Si es None (campo opcional
    ausente), no hace nada.
    """
    if not bilang:
        return
    for locale in ('es', 'en'):
        value = bilang.get(locale)
        if value is None:
            continue
        cur.execute(
            """
            INSERT INTO translations
                (entity_type, entity_id, field, locale, value)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (entity_type, entity_id, field, locale)
                DO UPDATE SET value = EXCLUDED.value
            """,
            (entity_type, entity_id, field, locale, value),
        )


def _set_niche_priorities(
    cur: psycopg.Cursor,
    entity_type: str,
    entity_id: str,
    priority: dict[str, int] | None,
    niche_ids: dict[str, str],
) -> None:
    """Inserta las filas de priority por niche de una entidad."""
    if not priority:
        return
    for niche_slug, value in priority.items():
        niche_id = niche_ids.get(niche_slug)
        if niche_id is None:
            continue
        cur.execute(
            """
            INSERT INTO niche_priorities
                (entity_type, entity_id, niche_id, priority)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (entity_type, entity_id, niche_id)
                DO UPDATE SET priority = EXCLUDED.priority
            """,
            (entity_type, entity_id, niche_id, value),
        )


def _link_niches(
    cur: psycopg.Cursor,
    table: str,
    entity_col: str,
    entity_id: str,
    niche_slugs: list[str] | None,
    niche_ids: dict[str, str],
) -> None:
    """Inserta las filas de la union `<entidad>_niches`."""
    # S608: `table`/`entity_col` son nombres de tabla/columna del propio
    # schema, no input externo. Los VALUES van parametrizados.
    query = f"""
        INSERT INTO "{table}" ({entity_col}, niche_id)
        VALUES (%s, %s)
        ON CONFLICT ({entity_col}, niche_id) DO NOTHING
        """  # noqa: S608
    for niche_slug in niche_slugs or []:
        niche_id = niche_ids.get(niche_slug)
        if niche_id is None:
            continue
        cur.execute(query, (entity_id, niche_id))


def _resolve_vocabulary(
    cur: psycopg.Cursor, table: str, names: set[str]
) -> dict[str, str]:
    """Inserta nombres deduplicados en `skills`/`tech_tags`/`niches` y
    devuelve el mapa `name -> id`. Idempotente sobre `name`/`slug`.
    """
    natural = 'slug' if table == 'niches' else 'name'
    out: dict[str, str] = {}
    for name in sorted(names):
        columns: dict[str, Any] = {natural: name}
        if table == 'niches':
            columns['position'] = _NICHES.index(name)
        out[name] = _upsert_returning_id(cur, table, natural, columns)
    return out


# ---------------------------------------------------------------------------
# Seeders por entidad
# ---------------------------------------------------------------------------


def _seed_profile(cur: psycopg.Cursor) -> None:
    p = _load_profile()
    contacts = p['contacts']
    profile_id = _upsert_returning_id(
        cur,
        'profile',
        'handle',
        {
            'name': p['name'],
            'handle': p['handle'],
            'location': p['location'],
            'email': contacts['email'],
            'phone': contacts.get('phone'),
            'linkedin_url': contacts['linkedin'],
            'github_url': contacts['github'],
            'website_url': contacts.get('website'),
            'avatar_url': p['avatarUrl'],
        },
    )
    _set_translation(cur, 'profile', profile_id, 'headline', p['headline'])
    _set_translation(cur, 'profile', profile_id, 'summary', p['summary'])
    _set_translation(
        cur, 'profile', profile_id, 'availability', p.get('availability')
    )
    stats = p.get('stats')
    if stats:
        cur.execute(
            """
            INSERT INTO profile_stats
                (profile_id, years_experience, companies, countries,
                 certifications)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (profile_id) DO UPDATE SET
                years_experience = EXCLUDED.years_experience,
                companies = EXCLUDED.companies,
                countries = EXCLUDED.countries,
                certifications = EXCLUDED.certifications
            """,
            (
                profile_id,
                stats['yearsExperience'],
                stats['companies'],
                stats['countries'],
                stats['certifications'],
            ),
        )


def _seed_experiences(
    cur: psycopg.Cursor, niche_ids: dict[str, str]
) -> dict[str, str]:
    """Inserta experiencias + bullets + uniones. Devuelve slug -> id."""
    ids: dict[str, str] = {}
    for slug, data in _load_dir('experiences'):
        exp_id = _upsert_returning_id(
            cur,
            'experiences',
            'slug',
            {
                'slug': slug,
                'company': data['company'],
                'company_url': data.get('companyUrl'),
                'start_ym': data['start'],
                'end_ym': data.get('end'),
                'seniority': data['seniority'],
            },
        )
        ids[slug] = exp_id
        _set_translation(cur, 'experience', exp_id, 'role', data['role'])
        _link_niches(
            cur,
            'experience_niches',
            'experience_id',
            exp_id,
            data.get('niches'),
            niche_ids,
        )
        _set_niche_priorities(
            cur, 'experience', exp_id, data.get('priority'), niche_ids
        )
        _seed_experience_bullets(cur, exp_id, data)
    return ids


def _seed_experience_bullets(
    cur: psycopg.Cursor, exp_id: str, data: dict[str, Any]
) -> None:
    """Inserta los bullets (responsibilities + achievements) de una
    experiencia. El bullet es idempotente sobre (experience_id, kind,
    position); su texto bilingue va a translations.
    """
    for kind, yaml_key in (
        ('responsibility', 'responsibilities'),
        ('achievement', 'achievements'),
    ):
        block = data.get(yaml_key) or {}
        es_list = block.get('es') or []
        en_list = block.get('en') or []
        for position in range(max(len(es_list), len(en_list))):
            cur.execute(
                """
                INSERT INTO experience_bullets
                    (experience_id, kind, position)
                VALUES (%s, %s, %s)
                ON CONFLICT (experience_id, kind, position) DO UPDATE
                    SET position = EXCLUDED.position
                RETURNING id
                """,
                (exp_id, kind, position),
            )
            bullet_id = _require_id(cur)
            bilang = {
                'es': es_list[position] if position < len(es_list) else None,
                'en': en_list[position] if position < len(en_list) else None,
            }
            _set_translation(
                cur, 'experience_bullet', bullet_id, 'text', bilang
            )


def _seed_experience_skills(
    cur: psycopg.Cursor,
    exp_id: str,
    data: dict[str, Any],
    skill_ids: dict[str, str],
) -> None:
    """Enlaza una experiencia con sus skills (technical + soft)."""
    for kind, yaml_key in (
        ('technical', 'skillsTechnical'),
        ('soft', 'skillsSoft'),
    ):
        for name in data.get(yaml_key) or []:
            skill_id = skill_ids.get(name)
            if skill_id is None:
                continue
            cur.execute(
                """
                INSERT INTO experience_skills
                    (experience_id, skill_id, kind)
                VALUES (%s, %s, %s)
                ON CONFLICT (experience_id, skill_id, kind) DO NOTHING
                """,
                (exp_id, skill_id, kind),
            )


def _seed_projects(
    cur: psycopg.Cursor,
    niche_ids: dict[str, str],
    tech_ids: dict[str, str],
) -> dict[str, str]:
    """Inserta proyectos + case studies + metricas + uniones."""
    ids: dict[str, str] = {}
    for slug, data in _load_dir('projects'):
        proj_id = _upsert_returning_id(
            cur,
            'projects',
            'slug',
            {
                'slug': slug,
                'name': data['name'],
                'url': data.get('url'),
                'repo': data.get('repo'),
                'status': data['status'],
                'project_type': data['projectType'],
                'is_confidential': data.get('isConfidential', False),
            },
        )
        ids[slug] = proj_id
        _set_translation(cur, 'project', proj_id, 'summary', data['summary'])
        _set_translation(
            cur, 'project', proj_id, 'description', data.get('description')
        )
        _set_translation(
            cur, 'project', proj_id, 'case_study', data.get('caseStudy')
        )
        _link_niches(
            cur,
            'project_niches',
            'project_id',
            proj_id,
            data.get('niches'),
            niche_ids,
        )
        _set_niche_priorities(
            cur, 'project', proj_id, data.get('priority'), niche_ids
        )
        _seed_project_stack(cur, proj_id, data, tech_ids)
        _seed_project_case_study(cur, proj_id, data)
        _seed_project_metrics(cur, proj_id, data)
    return ids


def _seed_project_stack(
    cur: psycopg.Cursor,
    proj_id: str,
    data: dict[str, Any],
    tech_ids: dict[str, str],
) -> None:
    """Enlaza un proyecto con su stack (`tech_tags`), preservando el orden."""
    for position, name in enumerate(data.get('stack') or []):
        tech_id = tech_ids.get(name)
        if tech_id is None:
            continue
        cur.execute(
            """
            INSERT INTO project_tech_tags (project_id, tech_tag_id, position)
            VALUES (%s, %s, %s)
            ON CONFLICT (project_id, tech_tag_id) DO UPDATE
                SET position = EXCLUDED.position
            """,
            (proj_id, tech_id, position),
        )


def _seed_project_case_study(
    cur: psycopg.Cursor, proj_id: str, data: dict[str, Any]
) -> None:
    """Inserta el case study detallado (1:1) de un proyecto, si existe."""
    detailed = data.get('caseStudyDetailed')
    if not detailed:
        return
    cs_id = _upsert_returning_id(
        cur,
        'project_case_studies',
        'project_id',
        {'project_id': proj_id},
    )
    for field in ('problem', 'process', 'result'):
        _set_translation(
            cur, 'project_case_study', cs_id, field, detailed.get(field)
        )


def _seed_project_metrics(
    cur: psycopg.Cursor, proj_id: str, data: dict[str, Any]
) -> None:
    """Inserta las metricas (par clave/valor ordenado) de un proyecto."""
    metrics = data.get('metrics') or {}
    for position, (key, value) in enumerate(metrics.items()):
        cur.execute(
            """
            INSERT INTO project_metrics
                (project_id, metric_key, metric_value, position)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (project_id, metric_key) DO UPDATE SET
                metric_value = EXCLUDED.metric_value,
                position = EXCLUDED.position
            """,
            (proj_id, key, str(value), position),
        )


def _seed_skill_categories(
    cur: psycopg.Cursor,
    niche_ids: dict[str, str],
    skill_ids: dict[str, str],
) -> None:
    """Inserta categorias de skills + sus uniones a skills y niches."""
    for slug, data in _load_dir('skills'):
        cat_id = _upsert_returning_id(
            cur,
            'skill_categories',
            'slug',
            {'slug': slug, 'kind': data['kind']},
        )
        _set_translation(cur, 'skill_category', cat_id, 'name', data['name'])
        _link_niches(
            cur,
            'skill_category_niches',
            'skill_category_id',
            cat_id,
            data.get('niches'),
            niche_ids,
        )
        for position, name in enumerate(data.get('skills') or []):
            skill_id = skill_ids.get(name)
            if skill_id is None:
                continue
            cur.execute(
                """
                INSERT INTO skill_category_skills
                    (skill_category_id, skill_id, position)
                VALUES (%s, %s, %s)
                ON CONFLICT (skill_category_id, skill_id) DO UPDATE
                    SET position = EXCLUDED.position
                """,
                (cat_id, skill_id, position),
            )


def _seed_simple_entities(
    cur: psycopg.Cursor, niche_ids: dict[str, str]
) -> None:
    """Inserta certificates, awards, education, references, languages,
    publications — entidades sin sub-tablas propias.
    """
    _seed_certificates(cur, niche_ids)
    _seed_awards(cur, niche_ids)
    _seed_education(cur, niche_ids)
    _seed_references(cur, niche_ids)
    _seed_languages(cur, niche_ids)
    _seed_publications(cur, niche_ids)


def _seed_certificates(cur: psycopg.Cursor, niche_ids: dict[str, str]) -> None:
    for slug, data in _load_dir('certificates'):
        cert_id = _upsert_returning_id(
            cur,
            'certificates',
            'slug',
            {
                'slug': slug,
                'title': data['title'],
                'issuer': data['issuer'],
                'issued_on': data['date'],
                'url': data['url'],
            },
        )
        _link_niches(
            cur,
            'certificate_niches',
            'certificate_id',
            cert_id,
            data.get('niches'),
            niche_ids,
        )


def _seed_awards(cur: psycopg.Cursor, niche_ids: dict[str, str]) -> None:
    for slug, data in _load_dir('awards'):
        award_id = _upsert_returning_id(
            cur,
            'awards',
            'slug',
            {
                'slug': slug,
                'issuer': data['issuer'],
                'awarded_ym': data['date'],
                'url': data.get('url'),
            },
        )
        _set_translation(cur, 'award', award_id, 'title', data['title'])
        _set_translation(
            cur, 'award', award_id, 'motivation', data['motivation']
        )
        _link_niches(
            cur,
            'award_niches',
            'award_id',
            award_id,
            data.get('niches'),
            niche_ids,
        )


def _seed_education(cur: psycopg.Cursor, niche_ids: dict[str, str]) -> None:
    for slug, data in _load_dir('education'):
        edu_id = _upsert_returning_id(
            cur,
            'education',
            'slug',
            {
                'slug': slug,
                'institution': data['institution'],
                'start_year': str(data['start']),
                'end_year': str(data['end']),
                'url': data.get('url'),
            },
        )
        _set_translation(cur, 'education', edu_id, 'degree', data.get('degree'))
        _set_translation(
            cur, 'education', edu_id, 'description', data['description']
        )
        _link_niches(
            cur,
            'education_niches',
            'education_id',
            edu_id,
            data.get('niches'),
            niche_ids,
        )


def _seed_references(cur: psycopg.Cursor, niche_ids: dict[str, str]) -> None:
    for slug, data in _load_dir('references'):
        ref_id = _upsert_returning_id(
            cur,
            'references',
            'slug',
            {
                'slug': slug,
                'name': data['name'],
                'role': data['role'],
                'company': data.get('company'),
                'linkedin_url': data['linkedin'],
            },
        )
        _set_translation(cur, 'reference', ref_id, 'relation', data['relation'])
        _link_niches(
            cur,
            'reference_niches',
            'reference_id',
            ref_id,
            data.get('niches'),
            niche_ids,
        )


def _seed_languages(cur: psycopg.Cursor, niche_ids: dict[str, str]) -> None:
    for slug, data in _load_dir('languages'):
        lang_id = _upsert_returning_id(cur, 'languages', 'slug', {'slug': slug})
        _set_translation(cur, 'language', lang_id, 'name', data['name'])
        _set_translation(cur, 'language', lang_id, 'level', data['level'])
        _link_niches(
            cur,
            'language_niches',
            'language_id',
            lang_id,
            data.get('niches'),
            niche_ids,
        )


def _seed_publications(cur: psycopg.Cursor, niche_ids: dict[str, str]) -> None:
    for slug, data in _load_dir('publications'):
        pub_id = _upsert_returning_id(
            cur,
            'publications',
            'slug',
            {
                'slug': slug,
                'title': data['title'],
                'platform': data['platform'],
                'url': data['url'],
                'canonical_url': data.get('canonical'),
                'published_on': data['date'],
            },
        )
        _set_translation(cur, 'publication', pub_id, 'summary', data['summary'])
        _link_niches(
            cur,
            'publication_niches',
            'publication_id',
            pub_id,
            data.get('niches'),
            niche_ids,
        )


# ---------------------------------------------------------------------------
# Recoleccion de vocabularios
# ---------------------------------------------------------------------------


def _collect_skill_names() -> set[str]:
    """Reune todos los nombres de skill: de `skill_categories.skills[]` y de
    `experience.skillsTechnical/skillsSoft`. Deduplicado.
    """
    names: set[str] = set()
    for _slug, data in _load_dir('skills'):
        names.update(data.get('skills') or [])
    for _slug, data in _load_dir('experiences'):
        names.update(data.get('skillsTechnical') or [])
        names.update(data.get('skillsSoft') or [])
    return names


def _collect_tech_names() -> set[str]:
    """Reune los nombres de tech tag del `stack[]` de todos los proyectos."""
    names: set[str] = set()
    for _slug, data in _load_dir('projects'):
        names.update(data.get('stack') or [])
    return names


# ---------------------------------------------------------------------------
# Orquestador
# ---------------------------------------------------------------------------


def run_seed(conn: psycopg.Connection) -> dict[str, int]:
    """Ejecuta el seed completo en una transaccion. Devuelve los conteos
    por tabla principal (para verificacion).
    """
    with conn.cursor() as cur:
        # 1. Vocabularios deduplicados.
        niche_ids = _resolve_vocabulary(cur, 'niches', set(_NICHES))
        skill_ids = _resolve_vocabulary(cur, 'skills', _collect_skill_names())
        tech_ids = _resolve_vocabulary(cur, 'tech_tags', _collect_tech_names())

        # 2. Entidades.
        _seed_profile(cur)
        exp_ids = _seed_experiences(cur, niche_ids)
        _seed_projects(cur, niche_ids, tech_ids)
        _seed_skill_categories(cur, niche_ids, skill_ids)
        _seed_simple_entities(cur, niche_ids)

        # 3. experience_skills (depende de experiences + skills ya cargados).
        for slug, data in _load_dir('experiences'):
            _seed_experience_skills(cur, exp_ids[slug], data, skill_ids)

        # 4. Conteos de verificacion.
        counts: dict[str, int] = {}
        for table in (
            'profile',
            'experiences',
            'projects',
            'skill_categories',
            'certificates',
            'awards',
            'education',
            'references',
            'languages',
            'publications',
            'niches',
            'skills',
            'tech_tags',
            'translations',
            'niche_priorities',
        ):
            cur.execute(f'SELECT count(*) FROM "{table}"')  # noqa: S608
            row = cur.fetchone()
            counts[table] = row[0] if row else 0
    conn.commit()
    return counts


def main() -> int:
    url = get_database_url()
    with psycopg.connect(url) as conn:
        counts = run_seed(conn)
    print('Seed completado. Conteos:')
    for table, n in counts.items():
        print(f'  {table:20s} {n}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
