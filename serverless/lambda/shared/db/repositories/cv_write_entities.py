"""@module cv_write_entities — upserts compuestos + deletes por entidad CV.

Cada upsert recibe el `data` dict en el SHAPE YAML del seed (camelCase:
`companyUrl`, `projectType`, bloques bilingues `{es, en}`, `niches`,
`priority`) y escribe la entidad COMPLETA: fila + hijos + uniones +
traducciones + prioridades. Los deletes limpian hijos, uniones,
traducciones polimorficas y prioridades antes de borrar la fila.

Los consumen el seed/restore de la Lambda `db` y la operation `content`
del Lambda `cv_admin`. Toda funcion asume que corre DENTRO de una
transaccion gestionada por el caller (`db_session()`).
"""

from __future__ import annotations

from typing import Any

from shared.db.models.cv.cv_entity import (
    Award,
    AwardNiche,
    Certificate,
    CertificateNiche,
    Endorsement,
    EndorsementNiche,
    Language,
    LanguageNiche,
    Publication,
    PublicationNiche,
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
from shared.db.models.taxonomy.catalog import TechTag
from shared.db.models.taxonomy.priority import NichePriority
from shared.db.repositories.cv_write import (
    coerce_date,
    delete_translations,
    ensure_named_vocab,
    link_niches,
    set_niche_priorities,
    set_translation,
    upsert_returning_id,
)
from shared.db.sa import Session, delete, select
from shared.db.sa import pg_insert as insert

# ---------------------------------------------------------------------------
# Profile (singleton)
# ---------------------------------------------------------------------------


def upsert_profile(
    session: Session,
    data: dict[str, Any],
    niche_ids: dict[str, str],
) -> str:
    """Upsert del profile (clave natural `handle`) + stats + i18n + niches."""
    contacts = data['contacts']
    profile_id = upsert_returning_id(
        session,
        Profile,
        'handle',
        {
            'name': data['name'],
            'handle': data['handle'],
            'location': data['location'],
            'email': contacts['email'],
            'phone': contacts.get('phone'),
            'linkedin_url': contacts['linkedin'],
            'github_url': contacts['github'],
            'website_url': contacts.get('website'),
            'avatar_url': data['avatarUrl'],
        },
    )
    set_translation(session, 'profile', profile_id, 'headline', data['headline'])
    set_translation(session, 'profile', profile_id, 'summary', data['summary'])
    set_translation(
        session, 'profile', profile_id, 'availability', data.get('availability')
    )
    stats = data.get('stats')
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
    link_niches(
        session,
        ProfileNiche,
        'profile_id',
        profile_id,
        data.get('niches'),
        niche_ids,
    )
    return profile_id


# ---------------------------------------------------------------------------
# Experience
# ---------------------------------------------------------------------------


def _replace_experience_bullets(
    session: Session, exp_id: str, data: dict[str, Any]
) -> None:
    """REEMPLAZA los bullets (y sus textos i18n) de una experiencia.

    delete + insert: una lista que se achico no deja bullets huerfanos
    (el upsert por posicion del seed viejo si los dejaba).
    """
    existing = (
        session.execute(
            select(ExperienceBullet.id).where(
                ExperienceBullet.experience_id == exp_id
            )
        )
        .scalars()
        .all()
    )
    if existing:
        delete_translations(session, 'experience_bullet', list(existing))
        session.execute(
            delete(ExperienceBullet).where(
                ExperienceBullet.experience_id == exp_id
            )
        )
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
                .returning(ExperienceBullet.id)
            )
            bullet_id = session.execute(stmt).scalar_one()
            bilang = {
                'es': es_list[position] if position < len(es_list) else None,
                'en': en_list[position] if position < len(en_list) else None,
            }
            set_translation(
                session, 'experience_bullet', bullet_id, 'text', bilang
            )


def _replace_experience_skills(
    session: Session,
    exp_id: str,
    data: dict[str, Any],
    skill_ids: dict[str, str],
) -> None:
    """REEMPLAZA las uniones experiencia<->skill (technical + soft)."""
    session.execute(
        delete(ExperienceSkill).where(ExperienceSkill.experience_id == exp_id)
    )
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


def upsert_experience(
    session: Session,
    data: dict[str, Any],
    niche_ids: dict[str, str],
    skill_ids: dict[str, str] | None = None,
) -> str:
    """Upsert completo de una experiencia (fila + bullets + skills + i18n).

    Si `skill_ids` es None (path API), los skills referenciados se
    upsertean al catalogo on-the-fly (mismo criterio que el seed).
    """
    if skill_ids is None:
        names = set(data.get('skillsTechnical') or []) | set(
            data.get('skillsSoft') or []
        )
        skill_ids = ensure_named_vocab(session, Skill, names)
    exp_id = upsert_returning_id(
        session,
        Experience,
        'slug',
        {
            'slug': data['slug'],
            'company': data['company'],
            'country': data['country'],
            'company_url': data.get('companyUrl'),
            'started_on': coerce_date(data['start']),
            'ended_on': coerce_date(data.get('end')),
            'seniority': data['seniority'],
            'metrics_estimated': data.get('metricsEstimated', False),
        },
    )
    set_translation(session, 'experience', exp_id, 'role', data['role'])
    if data.get('summary'):
        set_translation(session, 'experience', exp_id, 'summary', data['summary'])
    link_niches(
        session,
        ExperienceNiche,
        'experience_id',
        exp_id,
        data.get('niches'),
        niche_ids,
    )
    set_niche_priorities(
        session, 'experience', exp_id, data.get('priority'), niche_ids
    )
    _replace_experience_bullets(session, exp_id, data)
    _replace_experience_skills(session, exp_id, data, skill_ids)
    return exp_id


def delete_experience(session: Session, slug: str) -> bool:
    """Elimina una experiencia con TODOS sus hijos/uniones/i18n/priorities."""
    exp_id = session.execute(
        select(Experience.id).where(Experience.slug == slug)
    ).scalar_one_or_none()
    if exp_id is None:
        return False
    bullet_ids = (
        session.execute(
            select(ExperienceBullet.id).where(
                ExperienceBullet.experience_id == exp_id
            )
        )
        .scalars()
        .all()
    )
    delete_translations(session, 'experience_bullet', list(bullet_ids))
    session.execute(
        delete(ExperienceBullet).where(ExperienceBullet.experience_id == exp_id)
    )
    session.execute(
        delete(ExperienceSkill).where(ExperienceSkill.experience_id == exp_id)
    )
    session.execute(
        delete(ExperienceNiche).where(ExperienceNiche.experience_id == exp_id)
    )
    session.execute(
        delete(NichePriority).where(
            NichePriority.entity_type == 'experience',
            NichePriority.entity_id == exp_id,
        )
    )
    delete_translations(session, 'experience', [exp_id])
    session.execute(delete(Experience).where(Experience.id == exp_id))
    return True


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------


def _replace_project_stack(
    session: Session,
    proj_id: str,
    data: dict[str, Any],
    tech_ids: dict[str, str],
) -> None:
    """REEMPLAZA el stack (tech_tags ordenados) de un proyecto."""
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


def _upsert_project_case_study(
    session: Session, proj_id: str, data: dict[str, Any]
) -> None:
    """Upsert del case study detallado (1:1) + sus textos bilingues."""
    detailed = data.get('caseStudyDetailed')
    if not detailed:
        return
    cs_id = upsert_returning_id(
        session,
        ProjectCaseStudy,
        'project_id',
        {'project_id': proj_id},
    )
    for field in ('problem', 'process', 'result'):
        set_translation(
            session, 'project_case_study', cs_id, field, detailed.get(field)
        )


def _replace_project_metrics(
    session: Session, proj_id: str, data: dict[str, Any]
) -> None:
    """REEMPLAZA las metricas (pares clave/valor ordenados) de un proyecto."""
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


def upsert_project(
    session: Session,
    data: dict[str, Any],
    niche_ids: dict[str, str],
    tech_ids: dict[str, str] | None = None,
) -> str:
    """Upsert completo de un proyecto (fila + case study + metricas + stack)."""
    if tech_ids is None:
        tech_ids = ensure_named_vocab(
            session, TechTag, set(data.get('stack') or [])
        )
    proj_id = upsert_returning_id(
        session,
        Project,
        'slug',
        {
            'slug': data['slug'],
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
    set_translation(session, 'project', proj_id, 'summary', data['summary'])
    set_translation(
        session, 'project', proj_id, 'description', data.get('description')
    )
    set_translation(
        session, 'project', proj_id, 'case_study', data.get('caseStudy')
    )
    link_niches(
        session,
        ProjectNiche,
        'project_id',
        proj_id,
        data.get('niches'),
        niche_ids,
    )
    set_niche_priorities(
        session, 'project', proj_id, data.get('priority'), niche_ids
    )
    _replace_project_stack(session, proj_id, data, tech_ids)
    _upsert_project_case_study(session, proj_id, data)
    _replace_project_metrics(session, proj_id, data)
    return proj_id


def delete_project(session: Session, slug: str) -> bool:
    """Elimina un proyecto con case study, metricas, stack, i18n y demas."""
    proj_id = session.execute(
        select(Project.id).where(Project.slug == slug)
    ).scalar_one_or_none()
    if proj_id is None:
        return False
    cs_ids = (
        session.execute(
            select(ProjectCaseStudy.id).where(
                ProjectCaseStudy.project_id == proj_id
            )
        )
        .scalars()
        .all()
    )
    delete_translations(session, 'project_case_study', list(cs_ids))
    session.execute(
        delete(ProjectCaseStudy).where(ProjectCaseStudy.project_id == proj_id)
    )
    session.execute(
        delete(ProjectMetric).where(ProjectMetric.project_id == proj_id)
    )
    session.execute(
        delete(ProjectTechTag).where(ProjectTechTag.project_id == proj_id)
    )
    session.execute(
        delete(ProjectNiche).where(ProjectNiche.project_id == proj_id)
    )
    session.execute(
        delete(NichePriority).where(
            NichePriority.entity_type == 'project',
            NichePriority.entity_id == proj_id,
        )
    )
    delete_translations(session, 'project', [proj_id])
    session.execute(delete(Project).where(Project.id == proj_id))
    return True


# ---------------------------------------------------------------------------
# Skill categories
# ---------------------------------------------------------------------------


def upsert_skill_category(
    session: Session,
    data: dict[str, Any],
    niche_ids: dict[str, str],
    skill_ids: dict[str, str] | None = None,
) -> str:
    """Upsert de una categoria de skills + uniones ordenadas a skills."""
    if skill_ids is None:
        skill_ids = ensure_named_vocab(
            session, Skill, set(data.get('skills') or [])
        )
    cat_id = upsert_returning_id(
        session,
        SkillCategory,
        'slug',
        {'slug': data['slug'], 'kind': data['kind']},
    )
    set_translation(session, 'skill_category', cat_id, 'name', data['name'])
    link_niches(
        session,
        SkillCategoryNiche,
        'skill_category_id',
        cat_id,
        data.get('niches'),
        niche_ids,
    )
    set_niche_priorities(
        session, 'skill_category', cat_id, data.get('priority'), niche_ids
    )
    session.execute(
        delete(SkillCategorySkill).where(
            SkillCategorySkill.skill_category_id == cat_id
        )
    )
    for position, name in enumerate(data.get('skills') or []):
        skill_id = skill_ids.get(name)
        if skill_id is None:
            continue
        session.execute(
            insert(SkillCategorySkill).values(
                skill_category_id=cat_id,
                skill_id=skill_id,
                position=position,
            )
        )
    return cat_id


def delete_skill_category(session: Session, slug: str) -> bool:
    """Elimina una categoria de skills (uniones + i18n + priorities)."""
    cat_id = session.execute(
        select(SkillCategory.id).where(SkillCategory.slug == slug)
    ).scalar_one_or_none()
    if cat_id is None:
        return False
    session.execute(
        delete(SkillCategorySkill).where(
            SkillCategorySkill.skill_category_id == cat_id
        )
    )
    session.execute(
        delete(SkillCategoryNiche).where(
            SkillCategoryNiche.skill_category_id == cat_id
        )
    )
    session.execute(
        delete(NichePriority).where(
            NichePriority.entity_type == 'skill_category',
            NichePriority.entity_id == cat_id,
        )
    )
    delete_translations(session, 'skill_category', [cat_id])
    session.execute(delete(SkillCategory).where(SkillCategory.id == cat_id))
    return True


# ---------------------------------------------------------------------------
# Entidades simples (sin sub-tablas propias)
# ---------------------------------------------------------------------------


def upsert_certificate(
    session: Session, data: dict[str, Any], niche_ids: dict[str, str]
) -> str:
    cert_id = upsert_returning_id(
        session,
        Certificate,
        'slug',
        {
            'slug': data['slug'],
            'title': data['title'],
            'issuer': data['issuer'],
            'issued_on': coerce_date(data['date']),
            'url': data['url'],
        },
    )
    link_niches(
        session,
        CertificateNiche,
        'certificate_id',
        cert_id,
        data.get('niches'),
        niche_ids,
    )
    set_niche_priorities(
        session, 'certificate', cert_id, data.get('priority'), niche_ids
    )
    return cert_id


def upsert_award(
    session: Session, data: dict[str, Any], niche_ids: dict[str, str]
) -> str:
    award_id = upsert_returning_id(
        session,
        Award,
        'slug',
        {
            'slug': data['slug'],
            'issuer': data['issuer'],
            'awarded_on': coerce_date(data['date']),
            'url': data.get('url'),
        },
    )
    set_translation(session, 'award', award_id, 'title', data['title'])
    set_translation(session, 'award', award_id, 'motivation', data['motivation'])
    link_niches(
        session,
        AwardNiche,
        'award_id',
        award_id,
        data.get('niches'),
        niche_ids,
    )
    set_niche_priorities(
        session, 'award', award_id, data.get('priority'), niche_ids
    )
    return award_id


def upsert_education(
    session: Session, data: dict[str, Any], niche_ids: dict[str, str]
) -> str:
    edu_id = upsert_returning_id(
        session,
        EducationEntry,
        'slug',
        {
            'slug': data['slug'],
            'institution': data['institution'],
            'started_on': coerce_date(data['start']),
            'ended_on': coerce_date(data.get('end')),
            'url': data.get('url'),
        },
    )
    set_translation(session, 'education', edu_id, 'degree', data.get('degree'))
    set_translation(
        session, 'education', edu_id, 'description', data['description']
    )
    link_niches(
        session,
        EducationEntryNiche,
        'education_entry_id',
        edu_id,
        data.get('niches'),
        niche_ids,
    )
    set_niche_priorities(
        session, 'education', edu_id, data.get('priority'), niche_ids
    )
    return edu_id


def upsert_endorsement(
    session: Session, data: dict[str, Any], niche_ids: dict[str, str]
) -> str:
    end_id = upsert_returning_id(
        session,
        Endorsement,
        'slug',
        {
            'slug': data['slug'],
            'name': data['name'],
            'role': data['role'],
            'company': data.get('company'),
            'linkedin_url': data['linkedin'],
        },
    )
    set_translation(session, 'endorsement', end_id, 'relation', data['relation'])
    link_niches(
        session,
        EndorsementNiche,
        'endorsement_id',
        end_id,
        data.get('niches'),
        niche_ids,
    )
    set_niche_priorities(
        session, 'endorsement', end_id, data.get('priority'), niche_ids
    )
    return end_id


def upsert_language(
    session: Session, data: dict[str, Any], niche_ids: dict[str, str]
) -> str:
    lang_id = upsert_returning_id(
        session, Language, 'slug', {'slug': data['slug']}
    )
    set_translation(session, 'language', lang_id, 'name', data['name'])
    set_translation(session, 'language', lang_id, 'level', data['level'])
    link_niches(
        session,
        LanguageNiche,
        'language_id',
        lang_id,
        data.get('niches'),
        niche_ids,
    )
    set_niche_priorities(
        session, 'language', lang_id, data.get('priority'), niche_ids
    )
    return lang_id


def upsert_publication(
    session: Session, data: dict[str, Any], niche_ids: dict[str, str]
) -> str:
    pub_id = upsert_returning_id(
        session,
        Publication,
        'slug',
        {
            'slug': data['slug'],
            'title': data['title'],
            'platform': data['platform'],
            'url': data['url'],
            'canonical_url': data.get('canonical'),
            'published_on': coerce_date(data['date']),
        },
    )
    set_translation(session, 'publication', pub_id, 'summary', data['summary'])
    link_niches(
        session,
        PublicationNiche,
        'publication_id',
        pub_id,
        data.get('niches'),
        niche_ids,
    )
    set_niche_priorities(
        session, 'publication', pub_id, data.get('priority'), niche_ids
    )
    return pub_id


# Registro de entidades simples: model, union, columna FK, entity_type.
# Lo usa `delete_simple` (y el cv_admin para resolver el delete generico).
SIMPLE_ENTITIES: dict[str, tuple[type, type, str, str]] = {
    'certificate': (Certificate, CertificateNiche, 'certificate_id', 'certificate'),
    'award': (Award, AwardNiche, 'award_id', 'award'),
    'education': (EducationEntry, EducationEntryNiche, 'education_entry_id', 'education'),
    'endorsement': (Endorsement, EndorsementNiche, 'endorsement_id', 'endorsement'),
    'language': (Language, LanguageNiche, 'language_id', 'language'),
    'publication': (Publication, PublicationNiche, 'publication_id', 'publication'),
}


def delete_simple(session: Session, entity: str, slug: str) -> bool:
    """Elimina una entidad simple por slug (uniones + i18n + priorities).

    `entity` es una clave de `SIMPLE_ENTITIES`.
    """
    model, union_model, entity_col, entity_type = SIMPLE_ENTITIES[entity]
    entity_id = session.execute(
        select(model.id).where(model.slug == slug)
    ).scalar_one_or_none()
    if entity_id is None:
        return False
    entity_col_attr = getattr(union_model, entity_col)
    session.execute(delete(union_model).where(entity_col_attr == entity_id))
    session.execute(
        delete(NichePriority).where(
            NichePriority.entity_type == entity_type,
            NichePriority.entity_id == entity_id,
        )
    )
    delete_translations(session, entity_type, [entity_id])
    session.execute(delete(model).where(model.id == entity_id))
    return True
