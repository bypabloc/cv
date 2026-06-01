"""@module shared.db.cv_repository — lectura del CV desde Neon.

Concentra las queries SQLAlchemy que el Lambda `cv` necesita para servir
el CV. El `core/` del Lambda NO importa `sqlalchemy`; consume estas
funciones (`from shared.db.cv_repository import ...`), igual que `db`,
`contact_form` y `tracking_writer` consumen `shared.db.repository` y
`shared.db.migrations`.

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

from shared.db.models.cv.cv_entity import (
    Award,
    AwardNiche,
    Certificate,
    CertificateNiche,
    Endorsement,
    EndorsementNiche,
    Language,
    LanguageNiche,
)
from shared.db.models.cv.education import EducationEntry, EducationEntryNiche
from shared.db.models.cv.experience import (
    Experience,
    ExperienceBullet,
    ExperienceNiche,
    ExperienceSkill,
)
from shared.db.models.cv.profile import Profile, ProfileNiche, ProfileStats
from shared.db.models.cv.project import (
    Project,
    ProjectCaseStudy,
    ProjectMetric,
    ProjectNiche,
    ProjectTechTag,
)
from shared.db.models.cv.skill import (
    Skill,
    SkillCategory,
    SkillCategoryNiche,
    SkillCategorySkill,
)
from shared.db.models.i18n.translation import Translation
from shared.db.models.taxonomy.catalog import Niche, TechTag
from shared.db.models.taxonomy.priority import NichePriority

from .repository import RepositoryError
from .session import db_session


def _ensure_locale(locale: str) -> str:
    """Devuelve un locale valido o 'es' por defecto."""
    return locale if locale in ('es', 'en') else 'es'


def _drop_nones(d: dict[str, Any]) -> dict[str, Any]:
    """Devuelve `d` sin las claves cuyo valor sea None.

    Los Zod schemas tratan los campos opcionales como `T | undefined` (la
    clave AUSENTE), no como `T | null`. El cv_repository genera dicts con
    `None` para FK opcionales (companyUrl, phone, etc.) — esto los elimina
    antes de serializar al cache JSON / respuesta del API.
    """
    return {k: v for k, v in d.items() if v is not None}


def _niches_or_omit(niches: list[str]) -> list[str] | None:
    """Devuelve `niches` o None si esta vacio.

    Para entidades con niches OPCIONAL en Zod (education, languages,
    references): una lista vacia provoca Zod `min(1)` error; en su lugar
    omitimos la clave entera. None se elimina con _drop_nones.
    """
    return niches if niches else None


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
    """Devuelve `{entity_id: priority}` para el niche dado (filtro activo).

    Si el niche es None, devuelve `{}` (sin prioridades aplicables).
    """
    if niche_slug is None or not entity_ids:
        return {}

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


def _all_priorities_by_entity(
    session: Session,
    entity_type: str,
    entity_ids: list[str],
) -> dict[str, dict[str, int]]:
    """Devuelve `{entity_id: {niche_slug: priority, ...}}` para TODOS los niches.

    A diferencia de `_priorities_map`, no filtra por un niche concreto: devuelve
    el priority por cada niche en el que la entidad lo declara. Coincide con el
    shape Zod `PriorityByNicheSchema`.
    """
    if not entity_ids:
        return {}

    stmt = (
        select(NichePriority.entity_id, Niche.slug, NichePriority.priority)
        .join(Niche, Niche.id == NichePriority.niche_id)
        .where(
            NichePriority.entity_type == entity_type,
            NichePriority.entity_id.in_(entity_ids),
        )
    )
    out: dict[str, dict[str, int]] = defaultdict(dict)
    for row in session.execute(stmt):
        out[row.entity_id][row.slug] = row.priority
    return out


def _niches_by_entity(
    session: Session,
    union_model: type,
    entity_col: str,
    entity_ids: list[str],
) -> dict[str, list[str]]:
    """Devuelve `{entity_id: [niche_slug, ...]}` ordenado por position canonica."""
    if not entity_ids:
        return {}

    entity_col_attr = getattr(union_model, entity_col)
    stmt = (
        select(entity_col_attr, Niche.slug)
        .join(Niche, Niche.id == union_model.niche_id)
        .where(entity_col_attr.in_(entity_ids))
        .order_by(Niche.display_order)
    )
    out: dict[str, list[str]] = defaultdict(list)
    for row in session.execute(stmt):
        # row es (entity_id, niche.slug)
        out[row[0]].append(row[1])
    return out


def _experience_skills_by_exp(
    session: Session,
    experience_ids: list[str],
) -> dict[str, dict[str, list[str]]]:
    """Devuelve `{exp_id: {'technical': [...], 'soft': [...]}}`."""
    if not experience_ids:
        return {}
    stmt = (
        select(
            ExperienceSkill.experience_id,
            ExperienceSkill.kind,
            Skill.name,
        )
        .join(Skill, Skill.id == ExperienceSkill.skill_id)
        .where(ExperienceSkill.experience_id.in_(experience_ids))
        .order_by(Skill.name)
    )
    out: dict[str, dict[str, list[str]]] = defaultdict(
        lambda: {'technical': [], 'soft': []}
    )
    for row in session.execute(stmt):
        out[row.experience_id][row.kind].append(row.name)
    return out


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
            from shared.db.models.taxonomy.catalog import Niche

            niches_stmt = (
                select(Niche.slug)
                .join(ProfileNiche, ProfileNiche.niche_id == Niche.id)
                .where(ProfileNiche.profile_id == profile.id)
                .order_by(Niche.display_order)
            )
            niche_slugs = [row[0] for row in session.execute(niches_stmt)]

            # availability es opcional en Zod: si no hay traduccion, el
            # campo se omite (no se envia {} vacio).
            availability = translations.get('availability') or None
            contacts = _drop_nones(
                {
                    'email': profile.email,
                    'phone': profile.phone,
                    'linkedin': profile.linkedin_url,
                    'github': profile.github_url,
                    'website': profile.website_url,
                },
            )
            result: dict[str, Any] = _drop_nones(
                {
                    # slug NO se expone: ProfileSchema (Zod) no lo declara
                    # (el profile es singleton, handle/slug serian alias).
                    'name': profile.name,
                    'handle': profile.handle,
                    'location': profile.location,
                    'avatarUrl': profile.avatar_url,
                    'contacts': contacts,
                    'headline': translations.get('headline', {}),
                    'summary': translations.get('summary', {}),
                    'availability': availability,
                    'niches': niche_slugs,
                },
            )
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
    """Devuelve las experiencias filtradas por niche en shape Zod.

    `responsibilities`/`achievements` se devuelven como
    `{es: [str,...], en: [str,...]}` (dos arrays paralelos ordenados por
    position) — el mismo shape que esperan los Zod schemas de
    `@portfolio/content`. `niches`, `priority` (por TODOS los niches),
    `skillsTechnical`, `skillsSoft` se incluyen siempre.
    """
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
            all_priorities = _all_priorities_by_entity(
                session, 'experience', ids
            )
            niches_by_exp = _niches_by_entity(
                session, ExperienceNiche, 'experience_id', ids
            )
            skills_by_exp = _experience_skills_by_exp(session, ids)

            # Bullets ordenados por position → shape Zod {es:[...], en:[...]}
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
            # Por (experience_id, kind) acumulamos las traducciones en
            # listas paralelas es[] / en[] ordenadas por position.
            bullets_by_exp: dict[str, dict[str, dict[str, list[str]]]] = (
                defaultdict(
                    lambda: {
                        'responsibility': {'es': [], 'en': []},
                        'achievement': {'es': [], 'en': []},
                    }
                )
            )
            for bullet in bullets_raw:
                texts = bullet_translations.get(bullet.id, {}).get('text', {})
                target = bullets_by_exp[bullet.experience_id][bullet.kind]
                # Si una traduccion falta, se omite el bullet en ESE locale
                # para no insertar None / empty (Zod rechaza min(1)).
                if texts.get('es'):
                    target['es'].append(texts['es'])
                if texts.get('en'):
                    target['en'].append(texts['en'])

            result: list[dict[str, Any]] = []
            for exp in experiences:
                summary = translations.get(exp.id, {}).get('summary') or None
                exp_dict: dict[str, Any] = _drop_nones(
                    {
                        'slug': exp.slug,
                        'company': exp.company,
                        'country': exp.country,
                        'companyUrl': exp.company_url,
                        # Schema externo del CV mantiene formato YYYY-MM
                        # (legacy del frontend); DB ahora persiste DATE.
                        'start': exp.started_on.strftime('%Y-%m'),
                        'end': (
                            exp.ended_on.strftime('%Y-%m')
                            if exp.ended_on
                            else None
                        ),
                        'seniority': exp.seniority,
                        'metricsEstimated': exp.metrics_estimated,
                        'role': translations.get(exp.id, {}).get('role', {}),
                        'summary': summary,
                        'responsibilities': bullets_by_exp[exp.id][
                            'responsibility'
                        ],
                        'achievements': bullets_by_exp[exp.id]['achievement'],
                        'niches': niches_by_exp.get(exp.id, []),
                        'priority': all_priorities.get(exp.id, {}),
                        'skillsTechnical': skills_by_exp[exp.id]['technical'],
                        'skillsSoft': skills_by_exp[exp.id]['soft'],
                    },
                )
                result.append(exp_dict)
            # Ordenar por priority del niche pedido (si aplica) desc.
            if priorities:
                result.sort(
                    key=lambda e: priorities.get(
                        next(
                            (
                                exp.id
                                for exp in experiences
                                if exp.slug == e['slug']
                            ),
                            '',
                        ),
                        0,
                    ),
                    reverse=True,
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
            all_priorities = _all_priorities_by_entity(session, 'project', ids)
            niches_by_proj = _niches_by_entity(
                session, ProjectNiche, 'project_id', ids
            )

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
                # description y caseStudy son opcionales: si no tienen
                # traducciones se omiten para que Zod no los rechace.
                description = (
                    translations.get(proj.id, {}).get('description') or None
                )
                case_study = (
                    translations.get(proj.id, {}).get('case_study') or None
                )
                proj_dict: dict[str, Any] = _drop_nones(
                    {
                        'slug': proj.slug,
                        'name': proj.name,
                        'url': proj.url,
                        'links': proj.links or None,
                        'repo': proj.repo,
                        'status': proj.status,
                        'projectType': proj.project_type,
                        'isConfidential': proj.is_confidential,
                        'metricsEstimated': proj.metrics_estimated,
                        'summary': translations.get(proj.id, {}).get(
                            'summary', {}
                        ),
                        'description': description,
                        'caseStudy': case_study,
                        'stack': stack_by_proj.get(proj.id, []),
                        'metrics': dict(metrics_by_proj.get(proj.id, {})),
                        'niches': niches_by_proj.get(proj.id, []),
                        'priority': all_priorities.get(proj.id, {}),
                    },
                )
                cs = cs_by_proj.get(proj.id)
                if cs is not None:
                    cs_texts = cs_translations.get(cs.id, {})
                    proj_dict['caseStudyDetailed'] = {
                        'problem': cs_texts.get('problem', {}),
                        'process': cs_texts.get('process', {}),
                        'result': cs_texts.get('result', {}),
                    }
                result.append(proj_dict)
            # Si se filtro por niche, ordenar por priority de ese niche desc.
            if priorities:
                result.sort(
                    key=lambda p: priorities.get(
                        next(
                            (
                                proj.id
                                for proj in projects
                                if proj.slug == p['slug']
                            ),
                            '',
                        ),
                        0,
                    ),
                    reverse=True,
                )
            return result
    except Exception as exc:  # pragma: no cover
        raise RepositoryError(f'projects query failed: {exc}') from exc


def list_certificates(*, niche: str | None = None) -> list[dict[str, Any]]:
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
            ids = [c.id for c in certificates]
            niches_by_cert = _niches_by_entity(
                session, CertificateNiche, 'certificate_id', ids
            )
            return [
                _drop_nones(
                    {
                        'slug': c.slug,
                        'title': c.title,
                        'issuer': c.issuer,
                        'date': (
                            c.issued_on.isoformat() if c.issued_on else None
                        ),
                        'url': c.url,
                        'niches': niches_by_cert.get(c.id, []),
                    },
                )
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
            niches_by_award = _niches_by_entity(
                session, AwardNiche, 'award_id', ids
            )
            return [
                _drop_nones(
                    {
                        'slug': a.slug,
                        'issuer': a.issuer,
                        'date': a.awarded_on.strftime('%Y-%m'),
                        'url': a.url,
                        'title': translations.get(a.id, {}).get('title', {}),
                        'motivation': translations.get(a.id, {}).get(
                            'motivation', {}
                        ),
                        'niches': niches_by_award.get(a.id, []),
                    },
                )
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
            stmt = select(EducationEntry)
            filtered_ids = _ids_for_niche(
                session, EducationEntryNiche, 'education_entry_id', niche
            )
            if filtered_ids is not None:
                if not filtered_ids:
                    return []
                stmt = stmt.where(EducationEntry.id.in_(filtered_ids))
            educations = list(session.execute(stmt).scalars())
            ids = [e.id for e in educations]
            translations = _translations_map(session, 'education', ids)
            niches_by_edu = _niches_by_entity(
                session, EducationEntryNiche, 'education_entry_id', ids
            )
            return [
                _drop_nones(
                    {
                        'slug': e.slug,
                        'institution': e.institution,
                        # Schema externo mantiene 'start'/'end' como str
                        # (legacy del frontend); DB persiste DATE.
                        'start': (
                            e.started_on.strftime('%Y')
                            if e.started_on
                            else None
                        ),
                        'end': (
                            e.ended_on.strftime('%Y') if e.ended_on else None
                        ),
                        'url': e.url,
                        'degree': translations.get(e.id, {}).get('degree')
                        or None,
                        'description': translations.get(e.id, {}).get(
                            'description', {}
                        ),
                        'niches': _niches_or_omit(niches_by_edu.get(e.id, [])),
                    },
                )
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
            niches_by_lang = _niches_by_entity(
                session, LanguageNiche, 'language_id', ids
            )
            return [
                _drop_nones(
                    {
                        'slug': language.slug,
                        'name': translations.get(language.id, {}).get(
                            'name', {}
                        ),
                        'level': translations.get(language.id, {}).get(
                            'level', {}
                        ),
                        'niches': _niches_or_omit(
                            niches_by_lang.get(language.id, [])
                        ),
                    },
                )
                for language in languages
            ]
    except Exception as exc:  # pragma: no cover
        raise RepositoryError(f'languages query failed: {exc}') from exc


def list_references(
    *, niche: str | None = None, locale: str = 'es'
) -> list[dict[str, Any]]:
    """Devuelve los endorsements filtrados por niche.

    Nombre legacy `list_references` preservado para no romper call-sites
    del controller (cambia en commit 10). entity_type DB ahora es
    'endorsement'.
    """
    _ = _ensure_locale(locale)
    niche = _ensure_niche(niche)
    try:
        with db_session() as session:
            stmt = select(Endorsement)
            filtered_ids = _ids_for_niche(
                session, EndorsementNiche, 'endorsement_id', niche
            )
            if filtered_ids is not None:
                if not filtered_ids:
                    return []
                stmt = stmt.where(Endorsement.id.in_(filtered_ids))
            references = list(session.execute(stmt).scalars())
            ids = [r.id for r in references]
            translations = _translations_map(session, 'endorsement', ids)
            niches_by_ref = _niches_by_entity(
                session, EndorsementNiche, 'endorsement_id', ids
            )
            return [
                _drop_nones(
                    {
                        'slug': r.slug,
                        'name': r.name,
                        'role': r.role,
                        'company': r.company,
                        'linkedin': r.linkedin_url,
                        'relation': translations.get(r.id, {}).get(
                            'relation', {}
                        ),
                        'niches': _niches_or_omit(niches_by_ref.get(r.id, [])),
                    },
                )
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
            niches_by_cat = _niches_by_entity(
                session, SkillCategoryNiche, 'skill_category_id', ids
            )

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
                    'niches': niches_by_cat.get(c.id, []),
                }
                for c in categories
            ]
    except Exception as exc:  # pragma: no cover
        raise RepositoryError(f'skill_categories query failed: {exc}') from exc


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
