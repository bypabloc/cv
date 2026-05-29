"""@module seed_service — carga la data del CV (YAML) en PostgreSQL.

Lee los archivos de `core/seeds/data/` y los inserta en el schema relacional
del CV usando los modelos SQLAlchemy de `shared.db.models`. NO usa `psycopg`
directo: la unica capa de acceso a Neon es el ORM de `shared.db`, igual que
el resto del backend.

Idempotencia: se usa `INSERT ... ON CONFLICT ... DO UPDATE` via el dialecto
PostgreSQL de SQLAlchemy (`sqlalchemy.dialects.postgresql.insert`). Cada
fila se inserta con su clave natural (`slug` o clave compuesta) y, si ya
existe, se actualiza al mismo valor (no-op semantico) para devolver el ID.

Requisitos:
- El schema debe estar creado (`db/migrate`).
- `DATABASE_URL` o `SSM_NEON_URL_PATH` en el entorno (lo resuelve
  `shared.db.url`).

Estrategia:
1. Vocabularios deduplicados (`niches`, `skills`, `tech_tags`) primero.
2. Entidades (profile, experiences, projects, ...) — UUID resuelto por slug.
3. Estructuras hijas (bullets, case studies, metrics) y uniones N:M.
4. Traducciones polimorficas + niche_priorities al final (el trigger exige
   que la entidad ya exista).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from shared.db.models.cv import (
    Award,
    AwardNiche,
    Certificate,
    CertificateNiche,
    EducationEntry,
    EducationEntryNiche,
    Endorsement,
    EndorsementNiche,
    Experience,
    ExperienceBullet,
    ExperienceNiche,
    ExperienceSkill,
    Language,
    LanguageNiche,
    Profile,
    ProfileNiche,
    ProfileStats,
    Project,
    ProjectCaseStudy,
    ProjectMetric,
    ProjectNiche,
    ProjectTechTag,
    Publication,
    PublicationNiche,
    Skill,
    SkillCategory,
    SkillCategoryNiche,
    SkillCategorySkill,
)
from shared.db.models.i18n import Translation
from shared.db.models.taxonomy import Niche, NichePriority, TechTag
from shared.db.sa import Session, delete, func, select
from shared.db.sa import pg_insert as insert
from shared.db.seed_helpers import _parse_ym, _to_slug
from shared.db.session import db_session

# seeds/data/ vive dentro de core/ para que el packaging del deploy lo
# incluya en el zip (packaging.py solo copia core/ al artefacto). Este
# archivo esta en core/services/, asi que core/ es parents[1].
_CORE_DIR = Path(__file__).resolve().parents[1]
_DATA_DIR = _CORE_DIR / 'seeds' / 'data'

# Los 5 niches del portfolio, en orden canonico de presentacion.
_NICHES = ['fintech', 'architect', 'leader', 'vibe', 'generic']


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


# ---------------------------------------------------------------------------
# Helpers de upsert idempotente (SQLAlchemy)
# ---------------------------------------------------------------------------


def _upsert_returning_id(
    session: Session,
    model: type,
    natural_key: str,
    values: dict[str, Any],
) -> str:
    """Inserta una fila y devuelve su `id`. Idempotente sobre `natural_key`.

    Usa `INSERT ... ON CONFLICT (<natural_key>) DO UPDATE SET <field> =
    EXCLUDED.<field>` para TODOS los campos provistos (excepto el propio
    natural_key, que es la dimension de conflict). Asi un re-seed con
    cambios en el YAML propaga los valores nuevos a la fila existente.
    """
    excluded = insert(model).excluded
    update_set = {
        col: getattr(excluded, col) for col in values if col != natural_key
    }
    # Si el unico campo es el natural_key (no aplica aqui pero por seguridad),
    # caemos al patron viejo "no-op semantico" para evitar SET vacio.
    if not update_set:
        update_set = {natural_key: getattr(excluded, natural_key)}
    stmt = (
        insert(model)
        .values(**values)
        .on_conflict_do_update(
            index_elements=[natural_key],
            set_=update_set,
        )
        .returning(model.id)
    )
    return session.execute(stmt).scalar_one()


def _set_translation(
    session: Session,
    entity_type: str,
    entity_id: str,
    field: str,
    bilang: dict[str, str] | None,
) -> None:
    """Inserta (o actualiza) las filas es/en de un campo bilingue."""
    if not bilang:
        return
    for locale in ('es', 'en'):
        value = bilang.get(locale)
        if value is None:
            continue
        stmt = (
            insert(Translation)
            .values(
                entity_type=entity_type,
                entity_id=entity_id,
                field=field,
                locale=locale,
                value=value,
            )
            .on_conflict_do_update(
                index_elements=[
                    'entity_type',
                    'entity_id',
                    'field',
                    'locale',
                ],
                set_={'value': value},
            )
        )
        session.execute(stmt)


def _set_niche_priorities(
    session: Session,
    entity_type: str,
    entity_id: str,
    priority: dict[str, int] | None,
    niche_ids: dict[str, str],
) -> None:
    """Reescribe las filas de priority por niche de una entidad.

    Borra primero las existentes para esta entity y luego inserta las del
    YAML. Asi un YAML que removio un niche del bloque `priority` deja la
    DB consistente (sin entries huerfanas).
    """
    session.execute(
        delete(NichePriority).where(
            NichePriority.entity_type == entity_type,
            NichePriority.entity_id == entity_id,
        )
    )
    if not priority:
        return
    for niche_slug, value in priority.items():
        niche_id = niche_ids.get(niche_slug)
        if niche_id is None:
            continue
        session.execute(
            insert(NichePriority).values(
                entity_type=entity_type,
                entity_id=entity_id,
                niche_id=niche_id,
                priority=value,
            )
        )


def _link_niches(
    session: Session,
    union_model: type,
    entity_col: str,
    entity_id: str,
    niche_slugs: list[str] | None,
    niche_ids: dict[str, str],
) -> None:
    """Reescribe las filas de la union `<entidad>_niches`.

    Borra primero las existentes para esta entity y luego inserta las del
    YAML. Mantiene la DB sincronizada con la lista del seed (entradas
    huerfanas eliminadas).
    """
    entity_col_attr = getattr(union_model, entity_col)
    session.execute(
        delete(union_model).where(entity_col_attr == entity_id)
    )
    for niche_slug in niche_slugs or []:
        niche_id = niche_ids.get(niche_slug)
        if niche_id is None:
            continue
        session.execute(
            insert(union_model).values(
                **{entity_col: entity_id, 'niche_id': niche_id}
            )
        )


def _resolve_niches(session: Session) -> dict[str, str]:
    """Inserta los 5 niches del catalogo y devuelve `{slug: id}`."""
    out: dict[str, str] = {}
    for slug in _NICHES:
        nid = _upsert_returning_id(
            session,
            Niche,
            'slug',
            {'slug': slug, 'display_order': _NICHES.index(slug)},
        )
        out[slug] = nid
    return out


def _resolve_named_vocab(
    session: Session, model: type, names: set[str]
) -> dict[str, str]:
    """Upsert de un vocabulario con clave natural `slug` (cv_skills /
    tax_tech_tags). El `slug` se deriva del `name` via `_to_slug` (ASCII
    normalizado, kebab-case). El `name` se persiste como display canonico.
    """
    out: dict[str, str] = {}
    for name in sorted(names):
        slug = _to_slug(name)
        nid = _upsert_returning_id(
            session, model, 'slug', {'slug': slug, 'name': name}
        )
        out[name] = nid
    return out


# ---------------------------------------------------------------------------
# Seeders por entidad
# ---------------------------------------------------------------------------


def _seed_profile(session: Session, niche_ids: dict[str, str]) -> None:
    p = _load_profile()
    contacts = p['contacts']
    profile_id = _upsert_returning_id(
        session,
        Profile,
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
    _set_translation(session, 'profile', profile_id, 'headline', p['headline'])
    _set_translation(session, 'profile', profile_id, 'summary', p['summary'])
    _set_translation(
        session, 'profile', profile_id, 'availability', p.get('availability')
    )
    stats = p.get('stats')
    if stats:
        stmt = (
            insert(ProfileStats)
            .values(
                profile_id=profile_id,
                years_experience=stats['yearsExperience'],
                companies=stats['companies'],
                countries=stats['countries'],
                certifications=stats['certifications'],
            )
            .on_conflict_do_update(
                index_elements=['profile_id'],
                set_={
                    'years_experience': stats['yearsExperience'],
                    'companies': stats['companies'],
                    'countries': stats['countries'],
                    'certifications': stats['certifications'],
                },
            )
        )
        session.execute(stmt)
    _link_niches(
        session,
        ProfileNiche,
        'profile_id',
        profile_id,
        p.get('niches'),
        niche_ids,
    )


def _seed_experience_bullets(
    session: Session, exp_id: str, data: dict[str, Any]
) -> None:
    """Inserta los bullets (responsibilities + achievements) + sus textos."""
    for kind, yaml_key in (
        ('responsibility', 'responsibilities'),
        ('achievement', 'achievements'),
    ):
        block = data.get(yaml_key) or {}
        es_list = block.get('es') or []
        en_list = block.get('en') or []
        for position in range(max(len(es_list), len(en_list))):
            stmt = (
                insert(ExperienceBullet)
                .values(experience_id=exp_id, kind=kind, position=position)
                .on_conflict_do_update(
                    index_elements=['experience_id', 'kind', 'position'],
                    set_={'position': position},
                )
                .returning(ExperienceBullet.id)
            )
            bullet_id = session.execute(stmt).scalar_one()
            bilang = {
                'es': es_list[position] if position < len(es_list) else None,
                'en': en_list[position] if position < len(en_list) else None,
            }
            _set_translation(
                session, 'experience_bullet', bullet_id, 'text', bilang
            )


def _seed_experience_skills(
    session: Session,
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
            stmt = (
                insert(ExperienceSkill)
                .values(experience_id=exp_id, skill_id=skill_id, kind=kind)
                .on_conflict_do_nothing(
                    index_elements=['experience_id', 'skill_id', 'kind'],
                )
            )
            session.execute(stmt)


def _seed_experiences(
    session: Session, niche_ids: dict[str, str]
) -> dict[str, str]:
    """Inserta experiencias + bullets + uniones. Devuelve slug -> id."""
    ids: dict[str, str] = {}
    for slug, data in _load_dir('experiences'):
        exp_id = _upsert_returning_id(
            session,
            Experience,
            'slug',
            {
                'slug': slug,
                'company': data['company'],
                'country': data['country'],
                'company_url': data.get('companyUrl'),
                'started_on': _parse_ym(data['start']),
                'ended_on': _parse_ym(data.get('end')),
                'seniority': data['seniority'],
                'metrics_estimated': data.get('metricsEstimated', False),
            },
        )
        ids[slug] = exp_id
        _set_translation(session, 'experience', exp_id, 'role', data['role'])
        # summary es opcional pero la mayoria de YAMLs ya lo tienen; el
        # render del home lo usa para mostrar resumen corto en la timeline.
        if data.get('summary'):
            _set_translation(
                session, 'experience', exp_id, 'summary', data['summary']
            )
        _link_niches(
            session,
            ExperienceNiche,
            'experience_id',
            exp_id,
            data.get('niches'),
            niche_ids,
        )
        _set_niche_priorities(
            session, 'experience', exp_id, data.get('priority'), niche_ids
        )
        _seed_experience_bullets(session, exp_id, data)
    return ids


def _seed_project_stack(
    session: Session,
    proj_id: str,
    data: dict[str, Any],
    tech_ids: dict[str, str],
) -> None:
    """Reescribe el stack (`tech_tags`) de un proyecto preservando el orden.

    Borra las relaciones previas para asegurar que un tech removido del
    YAML quede fuera de la DB.
    """
    session.execute(
        delete(ProjectTechTag).where(ProjectTechTag.project_id == proj_id)
    )
    for position, name in enumerate(data.get('stack') or []):
        tech_id = tech_ids.get(name)
        if tech_id is None:
            continue
        session.execute(
            insert(ProjectTechTag).values(
                project_id=proj_id, tech_tag_id=tech_id, position=position
            )
        )


def _seed_project_case_study(
    session: Session, proj_id: str, data: dict[str, Any]
) -> None:
    """Inserta el case study detallado (1:1) de un proyecto, si existe."""
    detailed = data.get('caseStudyDetailed')
    if not detailed:
        return
    cs_id = _upsert_returning_id(
        session,
        ProjectCaseStudy,
        'project_id',
        {'project_id': proj_id},
    )
    for field in ('problem', 'process', 'result'):
        _set_translation(
            session, 'project_case_study', cs_id, field, detailed.get(field)
        )


def _seed_project_metrics(
    session: Session, proj_id: str, data: dict[str, Any]
) -> None:
    """Reescribe las metricas (par clave/valor ordenado) de un proyecto.

    Borra las metricas previas para que un YAML que removio una metrica
    deje la DB consistente.
    """
    session.execute(
        delete(ProjectMetric).where(ProjectMetric.project_id == proj_id)
    )
    metrics = data.get('metrics') or {}
    for position, (key, value) in enumerate(metrics.items()):
        session.execute(
            insert(ProjectMetric).values(
                project_id=proj_id,
                metric_key=key,
                metric_value=str(value),
                position=position,
            )
        )


def _seed_projects(
    session: Session,
    niche_ids: dict[str, str],
    tech_ids: dict[str, str],
) -> dict[str, str]:
    """Inserta proyectos + case studies + metricas + uniones."""
    ids: dict[str, str] = {}
    for slug, data in _load_dir('projects'):
        proj_id = _upsert_returning_id(
            session,
            Project,
            'slug',
            {
                'slug': slug,
                'name': data['name'],
                'url': data.get('url'),
                'links': data.get('links'),
                'repo': data.get('repo'),
                'status': data['status'],
                'project_type': data['projectType'],
                'is_confidential': data.get('isConfidential', False),
                'metrics_estimated': data.get('metricsEstimated', False),
            },
        )
        ids[slug] = proj_id
        _set_translation(
            session, 'project', proj_id, 'summary', data['summary']
        )
        _set_translation(
            session, 'project', proj_id, 'description', data.get('description')
        )
        _set_translation(
            session, 'project', proj_id, 'case_study', data.get('caseStudy')
        )
        _link_niches(
            session,
            ProjectNiche,
            'project_id',
            proj_id,
            data.get('niches'),
            niche_ids,
        )
        _set_niche_priorities(
            session, 'project', proj_id, data.get('priority'), niche_ids
        )
        _seed_project_stack(session, proj_id, data, tech_ids)
        _seed_project_case_study(session, proj_id, data)
        _seed_project_metrics(session, proj_id, data)
    return ids


def _seed_skill_categories(
    session: Session,
    niche_ids: dict[str, str],
    skill_ids: dict[str, str],
) -> None:
    """Inserta categorias de skills + sus uniones a skills y niches."""
    for slug, data in _load_dir('skills'):
        cat_id = _upsert_returning_id(
            session,
            SkillCategory,
            'slug',
            {'slug': slug, 'kind': data['kind']},
        )
        _set_translation(
            session, 'skill_category', cat_id, 'name', data['name']
        )
        _link_niches(
            session,
            SkillCategoryNiche,
            'skill_category_id',
            cat_id,
            data.get('niches'),
            niche_ids,
        )
        for position, name in enumerate(data.get('skills') or []):
            skill_id = skill_ids.get(name)
            if skill_id is None:
                continue
            stmt = (
                insert(SkillCategorySkill)
                .values(
                    skill_category_id=cat_id,
                    skill_id=skill_id,
                    position=position,
                )
                .on_conflict_do_update(
                    index_elements=['skill_category_id', 'skill_id'],
                    set_={'position': position},
                )
            )
            session.execute(stmt)


def _seed_certificates(
    session: Session, niche_ids: dict[str, str]
) -> None:
    for slug, data in _load_dir('certificates'):
        cert_id = _upsert_returning_id(
            session,
            Certificate,
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
            session,
            CertificateNiche,
            'certificate_id',
            cert_id,
            data.get('niches'),
            niche_ids,
        )


def _seed_awards(session: Session, niche_ids: dict[str, str]) -> None:
    for slug, data in _load_dir('awards'):
        award_id = _upsert_returning_id(
            session,
            Award,
            'slug',
            {
                'slug': slug,
                'issuer': data['issuer'],
                'awarded_on': _parse_ym(data['date']),
                'url': data.get('url'),
            },
        )
        _set_translation(session, 'award', award_id, 'title', data['title'])
        _set_translation(
            session, 'award', award_id, 'motivation', data['motivation']
        )
        _link_niches(
            session,
            AwardNiche,
            'award_id',
            award_id,
            data.get('niches'),
            niche_ids,
        )


def _seed_education(session: Session, niche_ids: dict[str, str]) -> None:
    for slug, data in _load_dir('education'):
        edu_id = _upsert_returning_id(
            session,
            EducationEntry,
            'slug',
            {
                'slug': slug,
                'institution': data['institution'],
                'started_on': _parse_ym(str(data['start'])),
                'ended_on': _parse_ym(str(data['end'])),
                'url': data.get('url'),
            },
        )
        _set_translation(
            session, 'education', edu_id, 'degree', data.get('degree')
        )
        _set_translation(
            session, 'education', edu_id, 'description', data['description']
        )
        _link_niches(
            session,
            EducationEntryNiche,
            'education_entry_id',
            edu_id,
            data.get('niches'),
            niche_ids,
        )


def _seed_endorsements(session: Session, niche_ids: dict[str, str]) -> None:
    """Antes `_seed_references`. Renombrado: ENUM entity_type pasa de
    'reference' a 'endorsement' tras la migracion group_tables_by_domain.
    """
    for slug, data in _load_dir('endorsements'):
        end_id = _upsert_returning_id(
            session,
            Endorsement,
            'slug',
            {
                'slug': slug,
                'name': data['name'],
                'role': data['role'],
                'company': data.get('company'),
                'linkedin_url': data['linkedin'],
            },
        )
        _set_translation(
            session, 'endorsement', end_id, 'relation', data['relation']
        )
        _link_niches(
            session,
            EndorsementNiche,
            'endorsement_id',
            end_id,
            data.get('niches'),
            niche_ids,
        )


def _seed_languages(session: Session, niche_ids: dict[str, str]) -> None:
    for slug, data in _load_dir('languages'):
        lang_id = _upsert_returning_id(
            session, Language, 'slug', {'slug': slug}
        )
        _set_translation(session, 'language', lang_id, 'name', data['name'])
        _set_translation(session, 'language', lang_id, 'level', data['level'])
        _link_niches(
            session,
            LanguageNiche,
            'language_id',
            lang_id,
            data.get('niches'),
            niche_ids,
        )


def _seed_publications(session: Session, niche_ids: dict[str, str]) -> None:
    for slug, data in _load_dir('publications'):
        pub_id = _upsert_returning_id(
            session,
            Publication,
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
        _set_translation(
            session, 'publication', pub_id, 'summary', data['summary']
        )
        _link_niches(
            session,
            PublicationNiche,
            'publication_id',
            pub_id,
            data.get('niches'),
            niche_ids,
        )


def _seed_simple_entities(
    session: Session, niche_ids: dict[str, str]
) -> None:
    """Inserta certificates, awards, education_entries, endorsements,
    languages, publications — entidades sin sub-tablas propias.
    """
    _seed_certificates(session, niche_ids)
    _seed_awards(session, niche_ids)
    _seed_education(session, niche_ids)
    _seed_endorsements(session, niche_ids)
    _seed_languages(session, niche_ids)
    _seed_publications(session, niche_ids)


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


def _run_seed_on_session(session: Session) -> dict[str, int]:
    """Ejecuta el seed completo dentro de la `session` provista. Devuelve los
    conteos por tabla principal (para verificacion).
    """
    # 1. Vocabularios deduplicados.
    niche_ids = _resolve_niches(session)
    skill_ids = _resolve_named_vocab(session, Skill, _collect_skill_names())
    tech_ids = _resolve_named_vocab(session, TechTag, _collect_tech_names())

    # 2. Entidades.
    _seed_profile(session, niche_ids)
    exp_ids = _seed_experiences(session, niche_ids)
    _seed_projects(session, niche_ids, tech_ids)
    _seed_skill_categories(session, niche_ids, skill_ids)
    _seed_simple_entities(session, niche_ids)

    # 3. experience_skills (depende de experiences + skills ya cargados).
    for slug, data in _load_dir('experiences'):
        _seed_experience_skills(session, exp_ids[slug], data, skill_ids)

    # 4. Conteos de verificacion: COUNT(*) por modelo via select.
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
