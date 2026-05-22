"""@module shared.db.cv_repository — lectura del CV desde Neon.

Concentra las queries SQLAlchemy que el Lambda `cv` necesita para servir
el CV. El `core/` del Lambda NO importa `sqlalchemy`; consume estas
funciones (`from shared.db.cv_repository import ...`), igual que `db` y
`stream_processor` consumen `shared.db.repository` y `shared.db.migrations`.

Filtros comunes:
- `niche` — opcional, `fintech|architect|leader|vibe|generic|None`. Cuando
  esta presente, filtra via la union `<entidad>_niches` y ordena por
  `niche_priorities.priority` desc (cuando aplica).
- `locale` — `es|en`. Selecciona la fila de `translations` por locale.

Shape de retorno:
Cada funcion devuelve dicts con el shape que esperan los Zod schemas de
`@portfolio/content` (camelCase). La traduccion se entrega como `{es, en}`
por campo bilingue para que el frontend pueda elegir el locale en runtime
sin re-consultar.

Cualquier error se traduce a `RepositoryError` (`shared.db.repository`),
que el `cv_service` del Lambda mapea a `ServiceError`.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import (
    Award,
    AwardNiche,
    Certificate,
    CertificateNiche,
    Education,
    EducationNiche,
    Experience,
    ExperienceBullet,
    ExperienceNiche,
    Language,
    LanguageNiche,
    NichePriority,
    Profile,
    ProfileNiche,
    ProfileStats,
    Project,
    ProjectCaseStudy,
    ProjectMetric,
    ProjectNiche,
    ProjectTechTag,
    Reference,
    ReferenceNiche,
    Skill,
    SkillCategory,
    SkillCategoryNiche,
    SkillCategorySkill,
    TechTag,
    Translation,
)
from .repository import RepositoryError
from .session import db_session


def _ensure_locale(locale: str) -> str:
    """Devuelve un locale valido o 'es' por defecto."""
    return locale if locale in ('es', 'en') else 'es'


def _ensure_niche(niche: str | None) -> str | None:
    """Valida el niche o devuelve None."""
    valid = {'fintech', 'architect', 'leader', 'vibe', 'generic'}
    return niche if niche in valid else None


def _translations_map(
    session: Session,
    entity_type: str,
    entity_ids: list[str],
) -> dict[str, dict[str, dict[str, str]]]:
    """Devuelve `{entity_id: {field: {locale: value}}}` para los IDs dados.

    Una sola query trae TODAS las traducciones de los IDs; el caller las
    indexa por entidad/campo.
    """
    if not entity_ids:
        return {}
    stmt = select(
        Translation.entity_id,
        Translation.field,
        Translation.locale,
        Translation.value,
    ).where(
        Translation.entity_type == entity_type,
        Translation.entity_id.in_(entity_ids),
    )
    out: dict[str, dict[str, dict[str, str]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    for row in session.execute(stmt):
        out[row.entity_id][row.field][row.locale] = row.value
    return out


def _ids_for_niche(
    session: Session,
    union_model: type,
    entity_col: str,
    niche_slug: str | None,
) -> set[str] | None:
    """Devuelve los entity_ids filtrados por niche o None si no hay filtro.

    Si `niche_slug` es None, devuelve None (sin filtro). Si existe, hace
    JOIN a `niches.slug` y devuelve el set de IDs.
    """
    if niche_slug is None:
        return None
    from .models import Niche

    entity_col_attr = getattr(union_model, entity_col)
    stmt = (
        select(entity_col_attr)
        .join(Niche, Niche.id == union_model.niche_id)
        .where(Niche.slug == niche_slug)
    )
    return {row[0] for row in session.execute(stmt)}


def _priorities_map(
    session: Session,
    entity_type: str,
    entity_ids: list[str],
    niche_slug: str | None,
) -> dict[str, int]:
    """Devuelve `{entity_id: priority}` para el niche dado.

    Si el niche es None, devuelve `{}` (sin prioridades aplicables).
    """
    if niche_slug is None or not entity_ids:
        return {}
    from .models import Niche

    stmt = (
        select(NichePriority.entity_id, NichePriority.priority)
        .join(Niche, Niche.id == NichePriority.niche_id)
        .where(
            NichePriority.entity_type == entity_type,
            NichePriority.entity_id.in_(entity_ids),
            Niche.slug == niche_slug,
        )
    )
    return {row.entity_id: row.priority for row in session.execute(stmt)}


def get_profile(*, locale: str = 'es') -> dict[str, Any]:
    """Devuelve el profile + stats + textos bilingues."""
    locale = _ensure_locale(locale)
    try:
        with db_session() as session:
            profile = session.execute(select(Profile)).scalar_one_or_none()
            if profile is None:
                return {}
            stats = session.execute(
                select(ProfileStats).where(
                    ProfileStats.profile_id == profile.id
                )
            ).scalar_one_or_none()
            translations = _translations_map(
                session, 'profile', [profile.id]
            ).get(profile.id, {})
            # Niches del profile (singleton).
            from .models import Niche

            niches_stmt = (
                select(Niche.slug)
                .join(ProfileNiche, ProfileNiche.niche_id == Niche.id)
                .where(ProfileNiche.profile_id == profile.id)
                .order_by(Niche.position)
            )
            niche_slugs = [row[0] for row in session.execute(niches_stmt)]

            result: dict[str, Any] = {
                'slug': profile.handle,
                'name': profile.name,
                'handle': profile.handle,
                'location': profile.location,
                'avatarUrl': profile.avatar_url,
                'contacts': {
                    'email': profile.email,
                    'phone': profile.phone,
                    'linkedin': profile.linkedin_url,
                    'github': profile.github_url,
                    'website': profile.website_url,
                },
                'headline': translations.get('headline', {}),
                'summary': translations.get('summary', {}),
                'availability': translations.get('availability', {}),
                'niches': niche_slugs,
            }
            if stats is not None:
                result['stats'] = {
                    'yearsExperience': stats.years_experience,
                    'companies': stats.companies,
                    'countries': stats.countries,
                    'certifications': stats.certifications,
                }
            return result
    except Exception as exc:  # pragma: no cover
        raise RepositoryError(f'profile query failed: {exc}') from exc


def list_experiences(
    *, niche: str | None = None, locale: str = 'es'
) -> list[dict[str, Any]]:
    """Devuelve las experiencias filtradas por niche, con bullets y skills."""
    _ = _ensure_locale(locale)
    niche = _ensure_niche(niche)
    try:
        with db_session() as session:
            stmt = select(Experience)
            filtered_ids = _ids_for_niche(
                session, ExperienceNiche, 'experience_id', niche
            )
            if filtered_ids is not None:
                if not filtered_ids:
                    return []
                stmt = stmt.where(Experience.id.in_(filtered_ids))
            experiences = list(session.execute(stmt).scalars())
            ids = [e.id for e in experiences]
            translations = _translations_map(session, 'experience', ids)
            priorities = _priorities_map(session, 'experience', ids, niche)

            # Bullets por experiencia
            bullet_stmt = (
                select(ExperienceBullet)
                .where(ExperienceBullet.experience_id.in_(ids))
                .order_by(ExperienceBullet.position)
            )
            bullets_raw = list(session.execute(bullet_stmt).scalars())
            bullet_ids = [b.id for b in bullets_raw]
            bullet_translations = _translations_map(
                session, 'experience_bullet', bullet_ids
            )
            bullets_by_exp: dict[str, dict[str, list[dict[str, str]]]] = (
                defaultdict(lambda: {'responsibility': [], 'achievement': []})
            )
            for bullet in bullets_raw:
                texts = bullet_translations.get(bullet.id, {}).get('text', {})
                bullets_by_exp[bullet.experience_id][bullet.kind].append(texts)

            result: list[dict[str, Any]] = []
            for exp in experiences:
                exp_dict: dict[str, Any] = {
                    'slug': exp.slug,
                    'company': exp.company,
                    'country': exp.country,
                    'companyUrl': exp.company_url,
                    'start': exp.start_ym,
                    'end': exp.end_ym,
                    'seniority': exp.seniority,
                    'metricsEstimated': exp.metrics_estimated,
                    'role': translations.get(exp.id, {}).get('role', {}),
                    'responsibilities': bullets_by_exp[exp.id]['responsibility'],
                    'achievements': bullets_by_exp[exp.id]['achievement'],
                }
                if priorities:
                    exp_dict['priority'] = priorities.get(exp.id, 0)
                result.append(exp_dict)
            # Ordenar por priority desc cuando hay filtro de niche.
            if priorities:
                result.sort(
                    key=lambda e: e.get('priority', 0), reverse=True
                )
            return result
    except Exception as exc:  # pragma: no cover
        raise RepositoryError(f'experiences query failed: {exc}') from exc


def list_projects(
    *, niche: str | None = None, locale: str = 'es'
) -> list[dict[str, Any]]:
    """Devuelve los proyectos filtrados por niche, con stack + metrics."""
    _ = _ensure_locale(locale)
    niche = _ensure_niche(niche)
    try:
        with db_session() as session:
            stmt = select(Project)
            filtered_ids = _ids_for_niche(
                session, ProjectNiche, 'project_id', niche
            )
            if filtered_ids is not None:
                if not filtered_ids:
                    return []
                stmt = stmt.where(Project.id.in_(filtered_ids))
            projects = list(session.execute(stmt).scalars())
            ids = [p.id for p in projects]
            translations = _translations_map(session, 'project', ids)
            priorities = _priorities_map(session, 'project', ids, niche)

            # Stack (tech tags)
            stack_stmt = (
                select(
                    ProjectTechTag.project_id,
                    TechTag.name,
                    ProjectTechTag.position,
                )
                .join(TechTag, TechTag.id == ProjectTechTag.tech_tag_id)
                .where(ProjectTechTag.project_id.in_(ids))
                .order_by(ProjectTechTag.position)
            )
            stack_by_proj: dict[str, list[str]] = defaultdict(list)
            for row in session.execute(stack_stmt):
                stack_by_proj[row.project_id].append(row.name)

            # Metrics
            metrics_stmt = (
                select(ProjectMetric)
                .where(ProjectMetric.project_id.in_(ids))
                .order_by(ProjectMetric.position)
            )
            metrics_by_proj: dict[str, dict[str, str]] = defaultdict(dict)
            for metric in session.execute(metrics_stmt).scalars():
                metrics_by_proj[metric.project_id][metric.metric_key] = (
                    metric.metric_value
                )

            # Case studies
            cs_stmt = select(ProjectCaseStudy).where(
                ProjectCaseStudy.project_id.in_(ids)
            )
            case_studies = list(session.execute(cs_stmt).scalars())
            cs_by_proj = {cs.project_id: cs for cs in case_studies}
            cs_ids = [cs.id for cs in case_studies]
            cs_translations = _translations_map(
                session, 'project_case_study', cs_ids
            )

            result: list[dict[str, Any]] = []
            for proj in projects:
                proj_dict: dict[str, Any] = {
                    'slug': proj.slug,
                    'name': proj.name,
                    'url': proj.url,
                    'repo': proj.repo,
                    'status': proj.status,
                    'projectType': proj.project_type,
                    'isConfidential': proj.is_confidential,
                    'metricsEstimated': proj.metrics_estimated,
                    'summary': translations.get(proj.id, {}).get('summary', {}),
                    'description': translations.get(proj.id, {}).get(
                        'description', {}
                    ),
                    'caseStudy': translations.get(proj.id, {}).get(
                        'case_study', {}
                    ),
                    'stack': stack_by_proj.get(proj.id, []),
                    'metrics': dict(metrics_by_proj.get(proj.id, {})),
                }
                cs = cs_by_proj.get(proj.id)
                if cs is not None:
                    cs_texts = cs_translations.get(cs.id, {})
                    proj_dict['caseStudyDetailed'] = {
                        'problem': cs_texts.get('problem', {}),
                        'process': cs_texts.get('process', {}),
                        'result': cs_texts.get('result', {}),
                    }
                if priorities:
                    proj_dict['priority'] = priorities.get(proj.id, 0)
                result.append(proj_dict)
            if priorities:
                result.sort(
                    key=lambda p: p.get('priority', 0), reverse=True
                )
            return result
    except Exception as exc:  # pragma: no cover
        raise RepositoryError(f'projects query failed: {exc}') from exc


def list_certificates(
    *, niche: str | None = None
) -> list[dict[str, Any]]:
    """Devuelve los certificados filtrados por niche."""
    niche = _ensure_niche(niche)
    try:
        with db_session() as session:
            stmt = select(Certificate)
            filtered_ids = _ids_for_niche(
                session, CertificateNiche, 'certificate_id', niche
            )
            if filtered_ids is not None:
                if not filtered_ids:
                    return []
                stmt = stmt.where(Certificate.id.in_(filtered_ids))
            certificates = list(session.execute(stmt).scalars())
            return [
                {
                    'slug': c.slug,
                    'title': c.title,
                    'issuer': c.issuer,
                    'date': c.issued_on.isoformat() if c.issued_on else None,
                    'url': c.url,
                }
                for c in certificates
            ]
    except Exception as exc:  # pragma: no cover
        raise RepositoryError(f'certificates query failed: {exc}') from exc


def list_awards(
    *, niche: str | None = None, locale: str = 'es'
) -> list[dict[str, Any]]:
    """Devuelve los premios filtrados por niche, con title/motivation bilingues."""
    _ = _ensure_locale(locale)
    niche = _ensure_niche(niche)
    try:
        with db_session() as session:
            stmt = select(Award)
            filtered_ids = _ids_for_niche(
                session, AwardNiche, 'award_id', niche
            )
            if filtered_ids is not None:
                if not filtered_ids:
                    return []
                stmt = stmt.where(Award.id.in_(filtered_ids))
            awards = list(session.execute(stmt).scalars())
            ids = [a.id for a in awards]
            translations = _translations_map(session, 'award', ids)
            return [
                {
                    'slug': a.slug,
                    'issuer': a.issuer,
                    'date': a.awarded_ym,
                    'url': a.url,
                    'title': translations.get(a.id, {}).get('title', {}),
                    'motivation': translations.get(a.id, {}).get(
                        'motivation', {}
                    ),
                }
                for a in awards
            ]
    except Exception as exc:  # pragma: no cover
        raise RepositoryError(f'awards query failed: {exc}') from exc


def list_education(
    *, niche: str | None = None, locale: str = 'es'
) -> list[dict[str, Any]]:
    """Devuelve la educacion filtrada por niche."""
    _ = _ensure_locale(locale)
    niche = _ensure_niche(niche)
    try:
        with db_session() as session:
            stmt = select(Education)
            filtered_ids = _ids_for_niche(
                session, EducationNiche, 'education_id', niche
            )
            if filtered_ids is not None:
                if not filtered_ids:
                    return []
                stmt = stmt.where(Education.id.in_(filtered_ids))
            educations = list(session.execute(stmt).scalars())
            ids = [e.id for e in educations]
            translations = _translations_map(session, 'education', ids)
            return [
                {
                    'slug': e.slug,
                    'institution': e.institution,
                    'start': e.start_year,
                    'end': e.end_year,
                    'url': e.url,
                    'degree': translations.get(e.id, {}).get('degree', {}),
                    'description': translations.get(e.id, {}).get(
                        'description', {}
                    ),
                }
                for e in educations
            ]
    except Exception as exc:  # pragma: no cover
        raise RepositoryError(f'education query failed: {exc}') from exc


def list_languages(
    *, niche: str | None = None, locale: str = 'es'
) -> list[dict[str, Any]]:
    """Devuelve los idiomas filtrados por niche."""
    _ = _ensure_locale(locale)
    niche = _ensure_niche(niche)
    try:
        with db_session() as session:
            stmt = select(Language)
            filtered_ids = _ids_for_niche(
                session, LanguageNiche, 'language_id', niche
            )
            if filtered_ids is not None:
                if not filtered_ids:
                    return []
                stmt = stmt.where(Language.id.in_(filtered_ids))
            languages = list(session.execute(stmt).scalars())
            ids = [language.id for language in languages]
            translations = _translations_map(session, 'language', ids)
            return [
                {
                    'slug': language.slug,
                    'name': translations.get(language.id, {}).get('name', {}),
                    'level': translations.get(language.id, {}).get('level', {}),
                }
                for language in languages
            ]
    except Exception as exc:  # pragma: no cover
        raise RepositoryError(f'languages query failed: {exc}') from exc


def list_references(
    *, niche: str | None = None, locale: str = 'es'
) -> list[dict[str, Any]]:
    """Devuelve las referencias filtradas por niche."""
    _ = _ensure_locale(locale)
    niche = _ensure_niche(niche)
    try:
        with db_session() as session:
            stmt = select(Reference)
            filtered_ids = _ids_for_niche(
                session, ReferenceNiche, 'reference_id', niche
            )
            if filtered_ids is not None:
                if not filtered_ids:
                    return []
                stmt = stmt.where(Reference.id.in_(filtered_ids))
            references = list(session.execute(stmt).scalars())
            ids = [r.id for r in references]
            translations = _translations_map(session, 'reference', ids)
            return [
                {
                    'slug': r.slug,
                    'name': r.name,
                    'role': r.role,
                    'company': r.company,
                    'linkedin': r.linkedin_url,
                    'relation': translations.get(r.id, {}).get('relation', {}),
                }
                for r in references
            ]
    except Exception as exc:  # pragma: no cover
        raise RepositoryError(f'references query failed: {exc}') from exc


def list_skill_categories(
    *, niche: str | None = None, locale: str = 'es'
) -> list[dict[str, Any]]:
    """Devuelve las categorias de skills filtradas por niche, con sus skills."""
    _ = _ensure_locale(locale)
    niche = _ensure_niche(niche)
    try:
        with db_session() as session:
            stmt = select(SkillCategory)
            filtered_ids = _ids_for_niche(
                session, SkillCategoryNiche, 'skill_category_id', niche
            )
            if filtered_ids is not None:
                if not filtered_ids:
                    return []
                stmt = stmt.where(SkillCategory.id.in_(filtered_ids))
            categories = list(session.execute(stmt).scalars())
            ids = [c.id for c in categories]
            translations = _translations_map(session, 'skill_category', ids)

            # Skills por categoria (ordenadas por position)
            skill_stmt = (
                select(
                    SkillCategorySkill.skill_category_id,
                    Skill.name,
                    SkillCategorySkill.position,
                )
                .join(Skill, Skill.id == SkillCategorySkill.skill_id)
                .where(SkillCategorySkill.skill_category_id.in_(ids))
                .order_by(SkillCategorySkill.position)
            )
            skills_by_cat: dict[str, list[str]] = defaultdict(list)
            for row in session.execute(skill_stmt):
                skills_by_cat[row.skill_category_id].append(row.name)

            return [
                {
                    'slug': c.slug,
                    'kind': c.kind,
                    'name': translations.get(c.id, {}).get('name', {}),
                    'skills': skills_by_cat.get(c.id, []),
                }
                for c in categories
            ]
    except Exception as exc:  # pragma: no cover
        raise RepositoryError(
            f'skill_categories query failed: {exc}'
        ) from exc


def get_full_cv(
    *, niche: str | None = None, locale: str = 'es'
) -> dict[str, Any]:
    """Devuelve el CV completo en un solo dict.

    Orquesta las funciones por entidad. Cada call abre/cierra su propia
    Session — el costo (Neon pooled) es despreciable frente al beneficio
    de mantener cada query autonoma.
    """
    return {
        'profile': get_profile(locale=locale),
        'experiences': list_experiences(niche=niche, locale=locale),
        'projects': list_projects(niche=niche, locale=locale),
        'certificates': list_certificates(niche=niche),
        'awards': list_awards(niche=niche, locale=locale),
        'education': list_education(niche=niche, locale=locale),
        'languages': list_languages(niche=niche, locale=locale),
        'references': list_references(niche=niche, locale=locale),
        'skillCategories': list_skill_categories(niche=niche, locale=locale),
    }
