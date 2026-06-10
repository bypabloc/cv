"""Modelos Pydantic de las entidades simples + delete/reorder/catalogs.

Espejo del shape YAML del seed para las entidades sin sub-tablas propias
(education, certificate, award, language, endorsement, publication) y los
payloads transversales: `DeleteIn` (delete-* por slug), `ReorderIn`
(reescritura de prioridades por niche) y `CatalogsIn` (sin payload).
"""

from __future__ import annotations

from typing import Literal

from shared.core.pydantic_types import BaseModel, ConfigDict, Field

from ._common import BiLang, FlexDate, PriorityMap, SlugStr, _Meta

# Entidades reordenables (las 9 con union `<entidad>_niches`).
ReorderEntityType = Literal[
    'experience',
    'project',
    'skill_category',
    'certificate',
    'award',
    'education',
    'language',
    'endorsement',
    'publication',
]


class EducationIn(BaseModel):
    """POST /cv-admin operation=content action=upsert-education."""

    slug: SlugStr
    institution: str = Field(min_length=1, max_length=200)
    start: FlexDate
    end: FlexDate | None = None
    url: str | None = None
    degree: BiLang | None = None
    description: BiLang
    niches: list[SlugStr] = Field(default_factory=list)
    priority: PriorityMap = Field(default_factory=dict)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class CertificateIn(BaseModel):
    """POST /cv-admin operation=content action=upsert-certificate."""

    slug: SlugStr
    title: str = Field(min_length=1, max_length=300)
    issuer: str = Field(min_length=1, max_length=200)
    date: FlexDate
    url: str = Field(min_length=1)
    niches: list[SlugStr] = Field(default_factory=list)
    priority: PriorityMap = Field(default_factory=dict)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class AwardIn(BaseModel):
    """POST /cv-admin operation=content action=upsert-award."""

    slug: SlugStr
    title: BiLang
    issuer: str = Field(min_length=1, max_length=200)
    date: FlexDate
    url: str | None = None
    motivation: BiLang
    niches: list[SlugStr] = Field(default_factory=list)
    priority: PriorityMap = Field(default_factory=dict)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class LanguageIn(BaseModel):
    """POST /cv-admin operation=content action=upsert-language."""

    slug: SlugStr
    name: BiLang
    level: BiLang
    niches: list[SlugStr] = Field(default_factory=list)
    priority: PriorityMap = Field(default_factory=dict)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class EndorsementIn(BaseModel):
    """POST /cv-admin operation=content action=upsert-endorsement."""

    slug: SlugStr
    name: str = Field(min_length=1, max_length=200)
    role: str = Field(min_length=1, max_length=200)
    relation: BiLang
    company: str | None = None
    linkedin: str = Field(min_length=1)
    niches: list[SlugStr] = Field(default_factory=list)
    priority: PriorityMap = Field(default_factory=dict)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class PublicationIn(BaseModel):
    """POST /cv-admin operation=content action=upsert-publication."""

    slug: SlugStr
    title: str = Field(min_length=1, max_length=300)
    platform: str = Field(min_length=1, max_length=200)
    url: str = Field(min_length=1)
    canonical: str | None = None
    date: FlexDate
    summary: BiLang
    niches: list[SlugStr] = Field(default_factory=list)
    priority: PriorityMap = Field(default_factory=dict)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class DeleteIn(BaseModel):
    """POST /cv-admin operation=content action=delete-<entidad>.

    Payload comun de TODOS los deletes: `{slug}`.
    """

    slug: SlugStr
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class ReorderIn(BaseModel):
    """POST /cv-admin operation=content action=reorder.

    Reescribe `tax_niche_priorities` del `(entity_type, niche)` segun el
    orden de `ordered_slugs` (prioridad descendente).
    """

    entity_type: ReorderEntityType
    niche: SlugStr
    ordered_slugs: list[SlugStr] = Field(min_length=1)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')


class CatalogsIn(BaseModel):
    """POST /cv-admin operation=content action=catalogs (sin payload)."""

    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = ConfigDict(populate_by_name=True, extra='ignore')
