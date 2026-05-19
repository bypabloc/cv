"""@module models — barrel del schema relacional del CV.

Importa `Base` y TODOS los modelos. `Base.metadata` queda poblada con cada
tabla, lo que lo hace el `target_metadata` unico para el autogenerate de
Alembic (`alembic/env.py` importa este modulo).

NO contiene logica — solo imports y re-exports.
"""

from .base import Base
from .base import TimestampMixin
from .base import UUIDPKMixin
from .catalog import Niche
from .catalog import Skill
from .catalog import TechTag
from .cv_entities import Award
from .cv_entities import Certificate
from .cv_entities import Education
from .cv_entities import Language
from .cv_entities import Publication
from .cv_entities import Reference
from .cv_entities import SkillCategory
from .enums import BulletKind
from .enums import EntityType
from .enums import Locale
from .enums import ProjectStatus
from .enums import ProjectType
from .enums import Seniority
from .enums import SkillKind
from .experience import Experience
from .experience import ExperienceBullet
from .junctions import AwardNiche
from .junctions import CertificateNiche
from .junctions import EducationNiche
from .junctions import ExperienceNiche
from .junctions import ExperienceSkill
from .junctions import LanguageNiche
from .junctions import ProjectNiche
from .junctions import ProjectTechTag
from .junctions import PublicationNiche
from .junctions import ReferenceNiche
from .junctions import SkillCategoryNiche
from .junctions import SkillCategorySkill
from .profile import Profile
from .profile import ProfileStats
from .project import Project
from .project import ProjectCaseStudy
from .project import ProjectMetric
from .translations import NichePriority
from .translations import Translation


__all__ = [
    'Award',
    'AwardNiche',
    'Base',
    'BulletKind',
    'Certificate',
    'CertificateNiche',
    'Education',
    'EducationNiche',
    'EntityType',
    'Experience',
    'ExperienceBullet',
    'ExperienceNiche',
    'ExperienceSkill',
    'Language',
    'LanguageNiche',
    'Locale',
    'Niche',
    'NichePriority',
    'Profile',
    'ProfileStats',
    'Project',
    'ProjectCaseStudy',
    'ProjectMetric',
    'ProjectNiche',
    'ProjectStatus',
    'ProjectTechTag',
    'ProjectType',
    'Publication',
    'PublicationNiche',
    'Reference',
    'ReferenceNiche',
    'Seniority',
    'Skill',
    'SkillCategory',
    'SkillCategoryNiche',
    'SkillCategorySkill',
    'SkillKind',
    'TechTag',
    'TimestampMixin',
    'Translation',
    'UUIDPKMixin',
]
