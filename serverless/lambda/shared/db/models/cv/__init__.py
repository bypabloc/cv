"""Re-exports planos del dominio CV."""

from .cv_entity import (
    Award,
    AwardNiche,
    Certificate,
    CertificateNiche,
    Language,
    LanguageNiche,
    Publication,
    PublicationNiche,
    Reference,
    ReferenceNiche,
)
from .education import Education, EducationNiche
from .experience import (
    Experience,
    ExperienceBullet,
    ExperienceNiche,
    ExperienceSkill,
)
from .profile import Profile, ProfileNiche, ProfileStats
from .project import (
    Project,
    ProjectCaseStudy,
    ProjectMetric,
    ProjectNiche,
    ProjectTechTag,
)
from .skill import (
    Skill,
    SkillCategory,
    SkillCategoryNiche,
    SkillCategorySkill,
)

__all__ = [
    'Award', 'AwardNiche',
    'Certificate', 'CertificateNiche',
    'Education', 'EducationNiche',
    'Experience', 'ExperienceBullet', 'ExperienceNiche', 'ExperienceSkill',
    'Language', 'LanguageNiche',
    'Profile', 'ProfileNiche', 'ProfileStats',
    'Project', 'ProjectCaseStudy', 'ProjectMetric',
    'ProjectNiche', 'ProjectTechTag',
    'Publication', 'PublicationNiche',
    'Reference', 'ReferenceNiche',
    'Skill', 'SkillCategory', 'SkillCategoryNiche', 'SkillCategorySkill',
]
