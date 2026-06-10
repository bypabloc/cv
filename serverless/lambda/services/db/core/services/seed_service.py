"""@module seed_service — restaura un snapshot del CV (YAML) en PostgreSQL.

El seed es el mecanismo de RESTORE del CV: baja un snapshot YAML
seed-compatible desde S3 (el que produce `devtools db_export` en
`s3://portfolio-db-backups-<stage>/{latest,history/<fecha>}/`) y lo
inserta en el schema relacional. La fuente de verdad del CV es la DB
(editada por el Lambda `cv_admin`); el snapshot es backup.

La logica de escritura (upserts idempotentes, traducciones, uniones de
niches, prioridades) vive en `shared.db.repositories.cv_write` /
`cv_write_entities` — la misma capa que usa la operation `content` del
Lambda `cv_admin`. Este modulo solo resuelve la fuente, carga los YAML y
orquesta.

Guard anti-pisada: si las tablas CV ya tienen datos, el seed ABORTA salvo
`confirm_overwrite: true` (SeedRequiresConfirmError) — restaurar sobre
ediciones vivas es una decision explicita, nunca un default.

Requisitos:
- El schema debe estar creado (`db/migrate`).
- `DATABASE_URL` o `SSM_NEON_URL_PATH` en el entorno (lo resuelve
  `shared.db.url`).
- `S3_DB_BACKUPS_BUCKET` (inyectada por devtools desde `uses.buckets`)
  cuando no se pasa un `source` explicito.

Estrategia:
1. Vocabularios deduplicados (`niches`, `skills`, `tech_tags`) primero.
2. Entidades (profile, experiences, projects, ...) — cada upsert compuesto
   escribe fila + hijos + uniones + traducciones + prioridades.
"""

from __future__ import annotations

import os
import tempfile
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

class SeedRequiresConfirmError(Exception):
    """Las tablas CV ya tienen datos y no vino `confirm_overwrite: true`."""


# ---------------------------------------------------------------------------
# Resolucion de la fuente del snapshot
# ---------------------------------------------------------------------------


def _default_source() -> str:
    """Prefijo S3 por defecto: el snapshot `latest/` del stage."""
    bucket = os.environ.get('S3_DB_BACKUPS_BUCKET', '')
    if not bucket:
        raise ValueError(
            'S3_DB_BACKUPS_BUCKET no esta definida y no se paso source; '
            'no hay snapshot que restaurar.'
        )
    return f's3://{bucket}/latest/'


def _download_snapshot(source: str) -> Path:
    """Baja un prefijo S3 `s3://bucket/prefix/` a un dir temporal local.

    Reconstruye el layout relativo (`<entidad>/<slug>.yaml`, `profile.yaml`)
    bajo el tempdir. Solo keys `.yaml`. En Lambda el unico filesystem
    escribible es el /tmp del runtime (tempfile lo usa por default).
    """
    from shared.aws.s3 import get_object_text, list_keys

    without_scheme = source.removeprefix('s3://')
    bucket, _, prefix = without_scheme.partition('/')
    if prefix and not prefix.endswith('/'):
        prefix += '/'
    target = Path(tempfile.mkdtemp(prefix='cv-seed-'))
    keys = [k for k in list_keys(bucket, prefix) if k.endswith('.yaml')]
    if not keys:
        raise ValueError(f'El snapshot {source} no contiene YAML alguno.')
    for key in keys:
        relative = key.removeprefix(prefix)
        dest = target / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(get_object_text(bucket, key), encoding='utf-8')
    return target


def _resolve_data_dir(source: str | None) -> Path:
    """Resuelve la fuente del snapshot a un directorio local.

    `source` None -> `latest/` del bucket del stage; `s3://...` -> se baja
    a un tempdir; cualquier otro valor se trata como path local (tests y
    runtime local).
    """
    resolved = source or _default_source()
    if resolved.startswith('s3://'):
        return _download_snapshot(resolved)
    return Path(resolved)


# ---------------------------------------------------------------------------
# Carga de YAML
# ---------------------------------------------------------------------------


def _load_dir(
    data_dir: Path, entity: str
) -> list[tuple[str, dict[str, Any]]]:
    """Carga todos los YAML de `<data_dir>/<entity>/`, ordenados por filename.

    Retorna `(slug, data)` por archivo. El slug se deriva del filename
    (igual que el frontend) cuando el YAML no lo declara.
    """
    folder = data_dir / entity
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


def _load_profile(data_dir: Path) -> dict[str, Any]:
    """Carga `<data_dir>/profile.yaml` (el singleton del CV).

    El formato es el que escribe `devtools db_export` (YAML plano con
    contacts/stats/headline/summary/availability/niches). El viejo
    `profile.ts` del seed original ya no se soporta: todo snapshot
    proviene del export.
    """
    return yaml.safe_load(
        (data_dir / 'profile.yaml').read_text(encoding='utf-8')
    )


def _with_slug(slug: str, data: dict[str, Any]) -> dict[str, Any]:
    """Inyecta el slug (derivado del filename si el YAML no lo trae)."""
    if data.get('slug') == slug:
        return data
    return {**data, 'slug': slug}


# ---------------------------------------------------------------------------
# Recoleccion de vocabularios
# ---------------------------------------------------------------------------


def _collect_skill_names(data_dir: Path) -> set[str]:
    """Reune todos los nombres de skill: de `skill_categories.skills[]` y de
    `experience.skillsTechnical/skillsSoft`. Deduplicado.
    """
    names: set[str] = set()
    for _slug, data in _load_dir(data_dir, 'skills'):
        names.update(data.get('skills') or [])
    for _slug, data in _load_dir(data_dir, 'experiences'):
        names.update(data.get('skillsTechnical') or [])
        names.update(data.get('skillsSoft') or [])
    return names


def _collect_tech_names(data_dir: Path) -> set[str]:
    """Reune los nombres de tech tag del `stack[]` de todos los proyectos."""
    names: set[str] = set()
    for _slug, data in _load_dir(data_dir, 'projects'):
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


def _has_cv_data(session: Session) -> bool:
    """True si las tablas CV principales ya tienen filas.

    Mira profile + experiences: cualquier env con CV cargado tiene al
    menos el profile; un env recien migrado tiene ambas en cero.
    """
    for model in (Profile, Experience):
        n = session.execute(select(func.count()).select_from(model)).scalar()
        if int(n or 0) > 0:
            return True
    return False


def _run_seed_on_session(session: Session, data_dir: Path) -> dict[str, int]:
    """Ejecuta el seed completo dentro de la `session` provista. Devuelve los
    conteos por tabla principal (para verificacion).
    """
    # 1. Vocabularios deduplicados.
    niche_ids = resolve_niches(session)
    skill_ids = ensure_named_vocab(
        session, Skill, _collect_skill_names(data_dir)
    )
    tech_ids = ensure_named_vocab(
        session, TechTag, _collect_tech_names(data_dir)
    )

    # 2. Entidades (cada upsert compuesto escribe hijos + uniones + i18n).
    upsert_profile(session, _load_profile(data_dir), niche_ids)
    for slug, data in _load_dir(data_dir, 'experiences'):
        upsert_experience(session, _with_slug(slug, data), niche_ids, skill_ids)
    for slug, data in _load_dir(data_dir, 'projects'):
        upsert_project(session, _with_slug(slug, data), niche_ids, tech_ids)
    for slug, data in _load_dir(data_dir, 'skills'):
        upsert_skill_category(
            session, _with_slug(slug, data), niche_ids, skill_ids
        )
    for folder, seeder in _SIMPLE_SEEDERS:
        for slug, data in _load_dir(data_dir, folder):
            seeder(session, _with_slug(slug, data), niche_ids)

    # 3. Conteos de verificacion: COUNT(*) por modelo via select.
    counts: dict[str, int] = {}
    for label, model in _COUNT_MODELS:
        n = session.execute(select(func.count()).select_from(model)).scalar()
        counts[label] = int(n or 0)
    return counts


def run_seed(
    source: str | None = None,
    confirm_overwrite: bool = False,
) -> dict[str, Any]:
    """Restaura un snapshot YAML del CV en PostgreSQL.

    Usa SQLAlchemy + `INSERT ... ON CONFLICT` (idempotente). El context
    manager `db_session()` commitea al salir limpio o hace rollback si
    levanta una excepcion.

    Parameters
    ----------
    source : str | None
        Prefijo S3 (`s3://bucket/prefix/`) o path local del snapshot.
        None usa `s3://$S3_DB_BACKUPS_BUCKET/latest/`.
    confirm_overwrite : bool
        Obligatorio en `true` cuando las tablas CV ya tienen datos
        (restaurar pisa las ediciones hechas via cv_admin).

    Returns
    -------
    dict[str, Any]
        `{'seeded': True, 'counts': {<tabla>: <filas>, ...}}` — conteos
        por tabla principal tras el seed.

    Raises
    ------
    SeedRequiresConfirmError
        Si hay datos y no vino `confirm_overwrite: true`.
    """
    with db_session() as session:
        if _has_cv_data(session) and not confirm_overwrite:
            raise SeedRequiresConfirmError(
                'Las tablas CV ya tienen datos (editados via cv_admin). '
                'Restaurar requiere confirm_overwrite: true.'
            )
    data_dir = _resolve_data_dir(source)
    with db_session() as session:
        counts = _run_seed_on_session(session, data_dir)
    return {'seeded': True, 'counts': counts}
