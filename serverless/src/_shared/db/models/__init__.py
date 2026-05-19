"""@module models — barrel del schema unificado del portfolio.

Importa TODOS los modelos (las 35 tablas: datos del visitante + contenido
del CV). Al importarse, `Base.metadata` queda poblada con cada tabla — es el
`target_metadata` unico del autogenerate de Alembic.

Import plano, sin jerarquia de dominio:
    from _shared.db.models import Contact, Experience, TrackingEvent

NO contiene logica — solo imports y re-exports.
"""

from .catalog import Niche, Skill, TechTag
from .contact import Contact
from .cv_entities import (
    Award,
    Certificate,
    Education,
    Language,
    Publication,
    Reference,
    SkillCategory,
)
from .experience import Experience, ExperienceBullet
from .junctions import (
    AwardNiche,
    CertificateNiche,
    EducationNiche,
    ExperienceNiche,
    ExperienceSkill,
    LanguageNiche,
    ProjectNiche,
    ProjectTechTag,
    PublicationNiche,
    ReferenceNiche,
    SkillCategoryNiche,
    SkillCategorySkill,
)
from .profile import Profile, ProfileStats
from .project import Project, ProjectCaseStudy, ProjectMetric
from .stream import ProcessedStreamEvent
from .tracking import EventType, TrackingEvent
from .translations import NichePriority, Translation

# Agrupado por dominio (visitante / CV), no alfabetico — RUF022 off a
# proposito: el agrupamiento documenta el origen de cada tabla.
__all__ = [  # noqa: RUF022
    # Datos del visitante (replica de DynamoDB)
    'Contact',
    'EventType',
    'ProcessedStreamEvent',
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
