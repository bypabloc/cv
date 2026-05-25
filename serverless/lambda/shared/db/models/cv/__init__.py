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

# DEPRECATED aliases — backward compat para call-sites legacy.
# Se eliminan en el commit 9 (refactor lambdas downstream) cuando todos
# los call-sites usen los nombres nuevos.
Education = EducationEntry              # noqa: F841
EducationNiche = EducationEntryNiche    # noqa: F841
Reference = Endorsement                 # noqa: F841
ReferenceNiche = EndorsementNiche       # noqa: F841

__all__ = [
    'Award', 'AwardNiche',
    'Certificate', 'CertificateNiche',
    'Education', 'EducationEntry',
    'EducationEntryNiche', 'EducationNiche',
    'Endorsement', 'EndorsementNiche',
    'Experience', 'ExperienceBullet', 'ExperienceNiche', 'ExperienceSkill',
    'Language', 'LanguageNiche',
    'Profile', 'ProfileNiche', 'ProfileStats',
    'Project', 'ProjectCaseStudy', 'ProjectMetric',
    'ProjectNiche', 'ProjectTechTag',
    'Publication', 'PublicationNiche',
    'Reference', 'ReferenceNiche',
    'Skill', 'SkillCategory', 'SkillCategoryNiche', 'SkillCategorySkill',
]
