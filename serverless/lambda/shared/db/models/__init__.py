"""@module models — barrel del schema unificado del portfolio.

Importa TODOS los modelos. Al importarse, `Base.metadata` queda poblada con
cada tabla — es el `target_metadata` unico del autogenerate de Alembic.

Organizado en 4 subpaquetes por dominio:
- `cv/`        — 28 tablas del CV
- `visitor/`   — 4 tablas del tracking
- `taxonomy/`  — 4 tablas de catalogos compartidos
- `i18n/`      — 1 tabla de traducciones

API publica preservada: `from shared.db.models import Profile` sigue
funcionando (los re-exports planos lo permiten).
"""

from .cv import (
    Award,
    AwardNiche,
    Certificate,
    CertificateNiche,
    Education,
    EducationNiche,
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
    Reference,
    ReferenceNiche,
    Skill,
    SkillCategory,
    SkillCategoryNiche,
    SkillCategorySkill,
)
from .i18n import Translation
from .taxonomy import EventType, Niche, NichePriority, TechTag
from .visitor import Contact, Session, SessionVisit, TrackingEvent

# Agrupado por dominio (visitante / CV / taxonomy / i18n) — RUF022 off a
# proposito: el agrupamiento documenta el origen de cada tabla.
__all__ = [  # noqa: RUF022
    # Datos del visitante
    'Contact',
    'EventType',
    'Session',
    'SessionVisit',
    'TrackingEvent',
    # Contenido del CV
    'Award',
    'AwardNiche',
    'Certificate',
    'CertificateNiche',
    'Education',
    'EducationNiche',
    'Experience',
    'ExperienceBullet',
    'ExperienceNiche',
    'ExperienceSkill',
    'Language',
    'LanguageNiche',
    'Niche',
    'NichePriority',
    'Profile',
    'ProfileNiche',
    'ProfileStats',
    'Project',
    'ProjectCaseStudy',
    'ProjectMetric',
    'ProjectNiche',
    'ProjectTechTag',
    'Publication',
    'PublicationNiche',
    'Reference',
    'ReferenceNiche',
    'Skill',
    'SkillCategory',
    'SkillCategoryNiche',
    'SkillCategorySkill',
    'TechTag',
    'Translation',
]
