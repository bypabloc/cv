"""@module seed_service — carga la data del CV (YAML) en PostgreSQL.

Lee los archivos de `core/seeds/data/` y los inserta en el schema relacional
del CV. La logica de escritura (upserts idempotentes, traducciones, uniones
de niches, prioridades) vive en `shared.db.repositories.cv_write` /
`cv_write_entities` — la misma capa que usa la operation `content` del
Lambda `cv_admin`. Este modulo solo carga los YAML y orquesta.

Requisitos:
- El schema debe estar creado (`db/migrate`).
- `DATABASE_URL` o `SSM_NEON_URL_PATH` en el entorno (lo resuelve
  `shared.db.url`).

Estrategia:
1. Vocabularios deduplicados (`niches`, `skills`, `tech_tags`) primero.
2. Entidades (profile, experiences, projects, ...) — cada upsert compuesto
   escribe fila + hijos + uniones + traducciones + prioridades.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from shared.db.models.cv.cv_entity import (
    Award,
    Certificate,
    Endorsement,
    Language,
    Publication,
)
from shared.db.models.cv.education import EducationEntry
from shared.db.models.cv.experience import Experience
from shared.db.models.cv.profile import Profile, ProfileNiche
from shared.db.models.cv.project import Project
from shared.db.models.cv.skill import Skill, SkillCategory
from shared.db.models.i18n.translation import Translation
from shared.db.models.taxonomy.catalog import Niche, TechTag
from shared.db.models.taxonomy.priority import NichePriority
from shared.db.repositories.cv_write import (
    ensure_named_vocab,
    resolve_niches,
)
from shared.db.repositories.cv_write_entities import (
    upsert_award,
    upsert_certificate,
    upsert_education,
    upsert_endorsement,
    upsert_experience,
    upsert_language,
    upsert_profile,
    upsert_project,
    upsert_publication,
    upsert_skill_category,
)
from shared.db.sa import Session, func, select
from shared.db.session import db_session

# seeds/data/ vive dentro de core/ para que el packaging del deploy lo
# incluya en el zip (packaging.py solo copia core/ al artefacto). Este
# archivo esta en core/services/, asi que core/ es parents[1].
_CORE_DIR = Path(__file__).resolve().parents[1]
_DATA_DIR = _CORE_DIR / 'seeds' / 'data'


# ---------------------------------------------------------------------------
# Carga de YAML
# ---------------------------------------------------------------------------


def _load_dir(entity: str) -> list[tuple[str, dict[str, Any]]]:
    """Carga todos los YAML de `seeds/data/<entity>/`, ordenados por filename.

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
    """Extrae el dict del profile del archivo TS `seeds/data/profile.ts`.

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
    return yaml.safe_load(_strip_ts_line_comments(block))


def _strip_ts_line_comments(block: str) -> str:
    """Elimina los comentarios de linea `//` de un bloque TS.

    Respeta los `//` que aparezcan dentro de un string (entre comillas
    simples o dobles): solo recorta a partir de un `//` que este fuera de
    comillas. YAML usa `#` para comentar, no `//`.
    """
    out: list[str] = []
    for line in block.splitlines():
        quote: str | None = None
        cut: int | None = None
        idx = 0
        while idx < len(line):
            char = line[idx]
            if quote is not None:
                if char == quote:
                    quote = None
            elif char in {'"', "'"}:
                quote = char
            elif char == '/' and idx + 1 < len(line) and line[idx + 1] == '/':
                cut = idx
                break
            idx += 1
        out.append(line if cut is None else line[:cut].rstrip())
    return '\n'.join(out)


def _with_slug(slug: str, data: dict[str, Any]) -> dict[str, Any]:
    """Inyecta el slug (derivado del filename si el YAML no lo trae)."""
    if data.get('slug') == slug:
        return data
    return {**data, 'slug': slug}


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

# Tablas principales sobre las que se reportan conteos tras el seed.
_COUNT_MODELS: tuple[tuple[str, type], ...] = (
    ('profile', Profile),
    ('profile_niches', ProfileNiche),
    ('experiences', Experience),
    ('projects', Project),
    ('skill_categories', SkillCategory),
    ('certificates', Certificate),
    ('awards', Award),
    ('education_entries', EducationEntry),
    ('endorsements', Endorsement),
    ('languages', Language),
    ('publications', Publication),
    ('niches', Niche),
    ('skills', Skill),
    ('tech_tags', TechTag),
    ('translations', Translation),
    ('niche_priorities', NichePriority),
)

# Entidades simples: carpeta YAML -> funcion de upsert compuesto.
_SIMPLE_SEEDERS = (
    ('certificates', upsert_certificate),
    ('awards', upsert_award),
    ('education', upsert_education),
    ('endorsements', upsert_endorsement),
    ('languages', upsert_language),
    ('publications', upsert_publication),
)


def _run_seed_on_session(session: Session) -> dict[str, int]:
    """Ejecuta el seed completo dentro de la `session` provista. Devuelve los
    conteos por tabla principal (para verificacion).
    """
    # 1. Vocabularios deduplicados.
    niche_ids = resolve_niches(session)
    skill_ids = ensure_named_vocab(session, Skill, _collect_skill_names())
    tech_ids = ensure_named_vocab(session, TechTag, _collect_tech_names())

    # 2. Entidades (cada upsert compuesto escribe hijos + uniones + i18n).
    upsert_profile(session, _load_profile(), niche_ids)
    for slug, data in _load_dir('experiences'):
        upsert_experience(session, _with_slug(slug, data), niche_ids, skill_ids)
    for slug, data in _load_dir('projects'):
        upsert_project(session, _with_slug(slug, data), niche_ids, tech_ids)
    for slug, data in _load_dir('skills'):
        upsert_skill_category(
            session, _with_slug(slug, data), niche_ids, skill_ids
        )
    for folder, seeder in _SIMPLE_SEEDERS:
        for slug, data in _load_dir(folder):
            seeder(session, _with_slug(slug, data), niche_ids)

    # 3. Conteos de verificacion: COUNT(*) por modelo via select.
    counts: dict[str, int] = {}
    for label, model in _COUNT_MODELS:
        n = session.execute(select(func.count()).select_from(model)).scalar()
        counts[label] = int(n or 0)
    return counts


def run_seed() -> dict[str, Any]:
    """Carga la data del CV (YAML de `core/seeds/data/`) en PostgreSQL.

    Usa SQLAlchemy + `INSERT ... ON CONFLICT` (idempotente). El context
    manager `db_session()` commitea al salir limpio o hace rollback si
    levanta una excepcion.

    Returns
    -------
    dict[str, Any]
        `{'seeded': True, 'counts': {<tabla>: <filas>, ...}}` — conteos
        por tabla principal tras el seed.
    """
    with db_session() as session:
        counts = _run_seed_on_session(session)
    return {'seeded': True, 'counts': counts}
