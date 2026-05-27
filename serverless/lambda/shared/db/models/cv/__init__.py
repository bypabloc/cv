"""Re-exports planos del dominio CV.

Renames respecto al schema previo:
- `Education` -> `EducationEntry` (tabla `cv_education_entries`)
- `EducationNiche` -> `EducationEntryNiche`
- `Reference` -> `Endorsement` (tabla `cv_endorsements`, `references` es
  palabra reservada SQL)
- `ReferenceNiche` -> `EndorsementNiche`
"""

from .cv_entity import (
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
from .education import EducationEntry, EducationEntryNiche
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
    'EducationEntry', 'EducationEntryNiche',
    'Endorsement', 'EndorsementNiche',
    'Experience', 'ExperienceBullet', 'ExperienceNiche', 'ExperienceSkill',
    'Language', 'LanguageNiche',
    'Profile', 'ProfileNiche', 'ProfileStats',
    'Project', 'ProjectCaseStudy', 'ProjectMetric',
    'ProjectNiche', 'ProjectTechTag',
    'Publication', 'PublicationNiche',
    'Skill', 'SkillCategory', 'SkillCategoryNiche', 'SkillCategorySkill',
]
