"""@module models — barrel del schema unificado post-rename.

Renames respecto al schema pre-rename (commit anterior):
- `Education` -> `EducationEntry`, `EducationNiche` -> `EducationEntryNiche`
- `Reference` -> `Endorsement`, `ReferenceNiche` -> `EndorsementNiche`

Las clases legacy `Education`, `Reference`, `EducationNiche`, `ReferenceNiche`
ya NO existen — callers deben usar los nuevos nombres.

API publica: `from shared.db.models import Profile, Contact, ...` sigue
funcionando para todas las clases sin rename.
"""

from .auth import (
    AuthAuditLog,
    AuthCodeKind,
    AuthCredentials,
    AuthEmailCode,
    AuthLinkKind,
    AuthMagicLink,
    AuthMfaKind,
    AuthMfaMethod,
    AuthMfaRecoveryCode,
    AuthUser,
    AuthUserAdminAction,
    AuthUserConsentLog,
    AuthUserSession,
    AuthUserStatus,
    AuthWebauthnCredential,
)
from .cv import (
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
from .i18n import Translation
from .taxonomy import EventType, Niche, NichePriority, TechTag
from .visitor import Contact, Session, SessionVisit, TrackingEvent

__all__ = [  # noqa: RUF022
    # Sistema auth (auth_)
    'AuthAuditLog',
    'AuthCodeKind',
    'AuthCredentials',
    'AuthEmailCode',
    'AuthLinkKind',
    'AuthMagicLink',
    'AuthMfaKind',
    'AuthMfaMethod',
    'AuthMfaRecoveryCode',
    'AuthUser',
    'AuthUserAdminAction',
    'AuthUserConsentLog',
    'AuthUserSession',
    'AuthUserStatus',
    'AuthWebauthnCredential',
    # Datos del visitante (vis_)
    'Contact',
    'EventType',
    'Session',
    'SessionVisit',
    'TrackingEvent',
    # Contenido del CV (cv_)
    'Award',
    'AwardNiche',
    'Certificate',
    'CertificateNiche',
    'EducationEntry',
    'EducationEntryNiche',
    'Endorsement',
    'EndorsementNiche',
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
    'Skill',
    'SkillCategory',
    'SkillCategoryNiche',
    'SkillCategorySkill',
    'TechTag',
    'Translation',
]
