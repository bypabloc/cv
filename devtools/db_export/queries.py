"""@module queries — lecturas SQL (read-only) de las entidades CV en Neon.

SQL crudo via psycopg v3 (devtools es autocontenido: NO importa
`serverless/`). Cada `fetch_*` reconstruye el dict YAML seed-compatible
de su entidad delegando el shape final en `serializer.py` (funciones
puras). Los ids se castean a `::text` para trabajar con strings planos.

Orden determinista:
- entidades: ORDER BY slug (= orden de archivos del seed).
- niches: ORDER BY tax_niches.display_order (orden canonico).
- bullets / metrics / stack / skills de categoria: por `position`.
- skills de experiencia: ORDER BY name (la union no tiene position).
"""

from dataclasses import dataclass
from typing import Any
from typing import Protocol

from psycopg import Connection
from psycopg.rows import dict_row

from db_export import serializer
from db_export.serializer import I18nFields
from db_export.serializer import YamlDict


# Un snapshot: carpeta -> lista de (slug, dict YAML). El profile va aparte.
type EntityEntries = list[tuple[str, YamlDict]]


class _SimpleSerializer(Protocol):
    """Firma uniforme de los serializers de entidades simples."""

    def __call__(
        self,
        row: dict[str, Any],
        *,
        fields: I18nFields | None,
        niches: list[str] | None,
        priority: dict[str, int] | None,
    ) -> YamlDict: ...


def _rows(
    conn: Connection,
    sql: str,
    params: tuple[Any, ...] = (),
) -> list[dict[str, Any]]:
    """Ejecuta un SELECT y devuelve las filas como dicts."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def _i18n(conn: Connection, entity_type: str) -> dict[str, I18nFields]:
    """Mapa `entity_id -> field -> {locale: value}` de un entity_type."""
    sql = (
        'SELECT entity_id::text AS entity_id, field, locale, value '
        'FROM i18n_translations WHERE entity_type = %s'
    )
    out: dict[str, I18nFields] = {}
    for row in _rows(conn, sql, (entity_type,)):
        fields = out.setdefault(row['entity_id'], {})
        fields.setdefault(row['field'], {})[row['locale']] = row['value']
    return out


def _niches(conn: Connection, table: str, fk: str) -> dict[str, list[str]]:
    """Mapa `entity_id -> [niche_slug]` en orden canonico (display_order)."""

    # y de los fetch_* (identificadores del codigo), nunca input externo.
    sql = (
        f'SELECT u.{fk}::text AS entity_id, n.slug FROM {table} u '  # noqa: S608
        'JOIN tax_niches n ON n.id = u.niche_id ORDER BY n.display_order'
    )
    out: dict[str, list[str]] = {}
    for row in _rows(conn, sql):
        out.setdefault(row['entity_id'], []).append(row['slug'])
    return out


def _priorities(
    conn: Connection,
    entity_type: str,
) -> dict[str, dict[str, int]]:
    """Mapa `entity_id -> {niche_slug: priority}` (orden canonico)."""
    sql = (
        'SELECT p.entity_id::text AS entity_id, n.slug, p.priority '
        'FROM tax_niche_priorities p '
        'JOIN tax_niches n ON n.id = p.niche_id '
        'WHERE p.entity_type = %s ORDER BY n.display_order'
    )
    out: dict[str, dict[str, int]] = {}
    for row in _rows(conn, sql, (entity_type,)):
        out.setdefault(row['entity_id'], {})[row['slug']] = row['priority']
    return out


def fetch_profile(conn: Connection) -> YamlDict | None:
    """Lee el profile singleton (+ stats + i18n + niches). None si no hay."""
    rows = _rows(
        conn,
        'SELECT id::text AS id, name, handle, location, email, phone, '
        'linkedin_url, github_url, website_url, avatar_url '
        'FROM cv_profiles ORDER BY handle LIMIT 1',
    )
    if not rows:
        return None
    row = rows[0]
    stats_rows = _rows(
        conn,
        'SELECT years_experience, companies, countries, certifications '
        'FROM cv_profile_stats WHERE profile_id = %s',
        (row['id'],),
    )
    fields = _i18n(conn, 'profile')
    niches = _niches(conn, 'cv_profile_niches', 'profile_id')
    return serializer.serialize_profile(
        row,
        stats=stats_rows[0] if stats_rows else None,
        fields=fields.get(row['id']),
        niches=niches.get(row['id']),
    )


def _experience_bullets(conn: Connection) -> dict[str, list[dict[str, Any]]]:
    """Bullets por experiencia con sus textos es/en ya unidos."""
    texts = _i18n(conn, 'experience_bullet')
    rows = _rows(
        conn,
        'SELECT id::text AS id, experience_id::text AS experience_id, '
        'kind::text AS kind, position FROM cv_experience_bullets',
    )
    out: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        text = (texts.get(row['id']) or {}).get('text') or {}
        out.setdefault(row['experience_id'], []).append(
            {
                'kind': row['kind'],
                'position': row['position'],
                'es': text.get('es'),
                'en': text.get('en'),
            }
        )
    return out


def _experience_skills(conn: Connection) -> dict[str, dict[str, list[str]]]:
    """Skills por experiencia: `{exp_id: {technical: [...], soft: [...]}}`."""
    rows = _rows(
        conn,
        'SELECT es.experience_id::text AS experience_id, '
        'es.kind::text AS kind, s.name '
        'FROM cv_experience_skills es '
        'JOIN cv_skills s ON s.id = es.skill_id ORDER BY s.name',
    )
    out: dict[str, dict[str, list[str]]] = {}
    for row in rows:
        per_exp = out.setdefault(row['experience_id'], {})
        per_exp.setdefault(row['kind'], []).append(row['name'])
    return out


def fetch_experiences(conn: Connection) -> EntityEntries:
    """Reconstruye los YAML de `experiences/` (bullets + skills + i18n)."""
    rows = _rows(
        conn,
        'SELECT id::text AS id, slug, company, country, company_url, '
        'started_on, ended_on, seniority::text AS seniority, '
        'metrics_estimated FROM cv_experiences ORDER BY slug',
    )
    fields = _i18n(conn, 'experience')
    bullets = _experience_bullets(conn)
    skills = _experience_skills(conn)
    niches = _niches(conn, 'cv_experience_niches', 'experience_id')
    priorities = _priorities(conn, 'experience')
    return [
        (
            row['slug'],
            serializer.serialize_experience(
                row,
                fields=fields.get(row['id']),
                bullets=bullets.get(row['id'], []),
                skills=skills.get(row['id'], {}),
                niches=niches.get(row['id']),
                priority=priorities.get(row['id']),
            ),
        )
        for row in rows
    ]


def fetch_projects(conn: Connection) -> EntityEntries:
    """Reconstruye los YAML de `projects/` (case study + metrics + stack)."""
    rows = _rows(
        conn,
        'SELECT id::text AS id, slug, name, url, links, repo, '
        'status::text AS status, project_type::text AS project_type, '
        'is_confidential, metrics_estimated FROM cv_projects ORDER BY slug',
    )
    fields = _i18n(conn, 'project')
    cs_fields = _i18n(conn, 'project_case_study')
    cs_by_project = {
        row['project_id']: cs_fields.get(row['id'])
        for row in _rows(
            conn,
            'SELECT id::text AS id, project_id::text AS project_id '
            'FROM cv_project_case_studies',
        )
    }
    metrics: dict[str, list[tuple[str, str]]] = {}
    for row in _rows(
        conn,
        'SELECT project_id::text AS project_id, metric_key, metric_value '
        'FROM cv_project_metrics ORDER BY project_id, position',
    ):
        metrics.setdefault(row['project_id'], []).append(
            (row['metric_key'], row['metric_value'])
        )
    stack: dict[str, list[str]] = {}
    for row in _rows(
        conn,
        'SELECT pt.project_id::text AS project_id, t.name '
        'FROM cv_project_tech_tags pt '
        'JOIN tax_tech_tags t ON t.id = pt.tech_tag_id '
        'ORDER BY pt.project_id, pt.position',
    ):
        stack.setdefault(row['project_id'], []).append(row['name'])
    niches = _niches(conn, 'cv_project_niches', 'project_id')
    priorities = _priorities(conn, 'project')
    return [
        (
            row['slug'],
            serializer.serialize_project(
                row,
                fields=fields.get(row['id']),
                case_study=cs_by_project.get(row['id']),
                metrics=metrics.get(row['id'], []),
                stack=stack.get(row['id'], []),
                niches=niches.get(row['id']),
                priority=priorities.get(row['id']),
            ),
        )
        for row in rows
    ]


def fetch_skill_categories(conn: Connection) -> EntityEntries:
    """Reconstruye los YAML de `skills/` (categorias + skills ordenadas)."""
    rows = _rows(
        conn,
        'SELECT id::text AS id, slug, kind::text AS kind '
        'FROM cv_skill_categories ORDER BY slug',
    )
    fields = _i18n(conn, 'skill_category')
    skills: dict[str, list[str]] = {}
    for row in _rows(
        conn,
        'SELECT scs.skill_category_id::text AS category_id, s.name '
        'FROM cv_skill_category_skills scs '
        'JOIN cv_skills s ON s.id = scs.skill_id '
        'ORDER BY scs.skill_category_id, scs.position',
    ):
        skills.setdefault(row['category_id'], []).append(row['name'])
    niches = _niches(conn, 'cv_skill_category_niches', 'skill_category_id')
    return [
        (
            row['slug'],
            serializer.serialize_skill_category(
                row,
                fields=fields.get(row['id']),
                skills=skills.get(row['id'], []),
                niches=niches.get(row['id']),
            ),
        )
        for row in rows
    ]


@dataclass(frozen=True)
class _SimpleSpec:
    """Config de una entidad simple (fila + niches + priority + i18n)."""

    sql: str
    entity_type: str
    niche_table: str
    niche_fk: str
    serialize: _SimpleSerializer
    has_i18n: bool = True


_SIMPLE_SPECS: dict[str, _SimpleSpec] = {
    'certificates': _SimpleSpec(
        sql=(
            'SELECT id::text AS id, slug, title, issuer, issued_on, url '
            'FROM cv_certificates ORDER BY slug'
        ),
        entity_type='certificate',
        niche_table='cv_certificate_niches',
        niche_fk='certificate_id',
        serialize=serializer.serialize_certificate,
        has_i18n=False,
    ),
    'awards': _SimpleSpec(
        sql=(
            'SELECT id::text AS id, slug, issuer, awarded_on, url '
            'FROM cv_awards ORDER BY slug'
        ),
        entity_type='award',
        niche_table='cv_award_niches',
        niche_fk='award_id',
        serialize=serializer.serialize_award,
    ),
    'education': _SimpleSpec(
        sql=(
            'SELECT id::text AS id, slug, institution, started_on, '
            'ended_on, url FROM cv_education_entries ORDER BY slug'
        ),
        entity_type='education',
        niche_table='cv_education_entry_niches',
        niche_fk='education_entry_id',
        serialize=serializer.serialize_education,
    ),
    'endorsements': _SimpleSpec(
        sql=(
            'SELECT id::text AS id, slug, name, role, company, '
            'linkedin_url FROM cv_endorsements ORDER BY slug'
        ),
        entity_type='endorsement',
        niche_table='cv_endorsement_niches',
        niche_fk='endorsement_id',
        serialize=serializer.serialize_endorsement,
    ),
    'languages': _SimpleSpec(
        sql='SELECT id::text AS id, slug FROM cv_languages ORDER BY slug',
        entity_type='language',
        niche_table='cv_language_niches',
        niche_fk='language_id',
        serialize=serializer.serialize_language,
    ),
    'publications': _SimpleSpec(
        sql=(
            'SELECT id::text AS id, slug, title, platform, url, '
            'canonical_url, published_on '
            'FROM cv_publications ORDER BY slug'
        ),
        entity_type='publication',
        niche_table='cv_publication_niches',
        niche_fk='publication_id',
        serialize=serializer.serialize_publication,
    ),
}


def _fetch_simple(conn: Connection, spec: _SimpleSpec) -> EntityEntries:
    """Lee una entidad simple completa segun su `_SimpleSpec`."""
    rows = _rows(conn, spec.sql)
    fields = _i18n(conn, spec.entity_type) if spec.has_i18n else {}
    niches = _niches(conn, spec.niche_table, spec.niche_fk)
    priorities = _priorities(conn, spec.entity_type)
    return [
        (
            row['slug'],
            spec.serialize(
                row,
                fields=fields.get(row['id']),
                niches=niches.get(row['id']),
                priority=priorities.get(row['id']),
            ),
        )
        for row in rows
    ]


def collect_snapshot(conn: Connection) -> dict[str, Any]:
    """Lee TODA la data CV y devuelve el snapshot seed-compatible.

    Returns
    -------
    dict
        `{'profile': dict | None, 'entities': {carpeta: [(slug, dict)]}}`
        con las 9 carpetas del seed (`experiences`, `projects`, `skills`,
        `certificates`, `awards`, `education`, `endorsements`,
        `languages`, `publications`).
    """
    entities: dict[str, EntityEntries] = {
        'experiences': fetch_experiences(conn),
        'projects': fetch_projects(conn),
        'skills': fetch_skill_categories(conn),
    }
    for folder, spec in _SIMPLE_SPECS.items():
        entities[folder] = _fetch_simple(conn, spec)
    return {'profile': fetch_profile(conn), 'entities': entities}
