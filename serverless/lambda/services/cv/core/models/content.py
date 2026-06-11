"""Modelos Pydantic de los upserts grandes de la operation `content`.

Espejo EXACTO del shape YAML de los snapshots (el que escribe
`devtools db_export` y consume el restore del Lambda db):
claves camelCase (`companyUrl`, `avatarUrl`, `skillsTechnical`, ...) via
`alias` + `populate_by_name=True`. Los services vuelcan el payload con
`model_dump(by_alias=True)` para entregarle a la capa de escritura
(`shared.db.repositories.cv_write_entities`) el mismo dict que el seed.

Los modelos validan SOLO la estructura (slug kebab-case, fechas, enums,
bloques bilingues). La pertenencia de los niches al catalogo la valida el
service (`UNKNOWN_NICHE`) antes de escribir.
"""

from __future__ import annotations

from typing import Any, Literal

from shared.core.pydantic_types import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)

from ._common import (
    BiLang,
    BulletsBlock,
    FlexDate,
    PriorityMap,
    SlugStr,
    _Meta,
)


class ProfileContacts(BaseModel):
    """Bloque `contacts` del profile (espejo del seed `profile.ts`)."""

    email: EmailStr
    phone: str | None = None
    linkedin: str = Field(min_length=1)
    github: str = Field(min_length=1)
    website: str | None = None

    model_config = ConfigDict(extra='ignore')


class ProfileStats(BaseModel):
    """Bloque `stats` del profile (contadores 1:1)."""

    years_experience: int = Field(alias='yearsExperience', ge=0)
    companies: int = Field(ge=0)
    countries: int = Field(ge=0)
    certifications: int = Field(ge=0)

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class ProfileIn(BaseModel):
    """POST /cv operation=content action=upsert-profile.

    Singleton: el upsert es por `handle` (clave natural).
    """

    name: str = Field(min_length=1, max_length=200)
    handle: SlugStr
    headline: BiLang
    summary: BiLang
    location: str = Field(min_length=1, max_length=200)
    availability: BiLang | None = None
    contacts: ProfileContacts
    avatar_url: str = Field(alias='avatarUrl', min_length=1)
    niches: list[SlugStr] = Field(default_factory=list)
    stats: ProfileStats | None = None
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class ExperienceIn(BaseModel):
    """POST /cv operation=content action=upsert-experience.

    Upsert completo: fila + bullets + skills + i18n + niches + priorities.
    """

    slug: SlugStr
    role: BiLang
    company: str = Field(min_length=1, max_length=200)
    country: str = Field(min_length=1, max_length=100)
    company_url: str | None = Field(default=None, alias='companyUrl')
    start: FlexDate
    end: FlexDate | None = None
    seniority: Literal['intern', 'junior', 'mid', 'senior', 'lead']
    summary: BiLang | None = None
    metrics_estimated: bool = Field(default=False, alias='metricsEstimated')
    responsibilities: BulletsBlock | None = None
    achievements: BulletsBlock | None = None
    skills_technical: list[str] = Field(
        default_factory=list, alias='skillsTechnical',
    )
    skills_soft: list[str] = Field(default_factory=list, alias='skillsSoft')
    niches: list[SlugStr] = Field(default_factory=list)
    priority: PriorityMap = Field(default_factory=dict)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class CaseStudyDetailed(BaseModel):
    """Bloque `caseStudyDetailed` del project (problem/process/result)."""

    problem: BiLang | None = None
    process: BiLang | None = None
    result: BiLang | None = None

    model_config = ConfigDict(extra='ignore')


class ProjectIn(BaseModel):
    """POST /cv operation=content action=upsert-project.

    Upsert completo: fila + case study + metricas + stack + i18n + niches
    + priorities.
    """

    slug: SlugStr
    name: str = Field(min_length=1, max_length=200)
    summary: BiLang
    description: BiLang | None = None
    url: str | None = None
    links: list[dict[str, Any]] | None = None
    repo: str | None = None
    status: Literal['active', 'inactive', 'concept']
    project_type: Literal[
        'web', 'mobile', 'cli', 'library', 'ai', 'fintech-platform',
    ] = Field(alias='projectType')
    is_confidential: bool = Field(default=False, alias='isConfidential')
    metrics_estimated: bool = Field(default=False, alias='metricsEstimated')
    stack: list[str] = Field(default_factory=list)
    case_study: BiLang | None = Field(default=None, alias='caseStudy')
    case_study_detailed: CaseStudyDetailed | None = Field(
        default=None, alias='caseStudyDetailed',
    )
    metrics: dict[str, Any] = Field(default_factory=dict)
    niches: list[SlugStr] = Field(default_factory=list)
    priority: PriorityMap = Field(default_factory=dict)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class SkillCategoryIn(BaseModel):
    """POST /cv operation=content action=upsert-skill-category.

    Upsert de la categoria + uniones ORDENADAS a skills (el orden de
    `skills` es el orden de presentacion).
    """

    slug: SlugStr
    name: BiLang
    kind: Literal['technical', 'soft']
    skills: list[str] = Field(default_factory=list)
    niches: list[SlugStr] = Field(default_factory=list)
    priority: PriorityMap = Field(default_factory=dict)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')
