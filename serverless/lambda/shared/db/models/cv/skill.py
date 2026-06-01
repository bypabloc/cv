"""@module cv.skill — catalogo skill + categoria + junctions.

`Skill` y `TechTag` ahora tienen `slug` UNIQUE (kebab-case ASCII) +
`name` (display casing). El slug se deriva del name via `_to_slug()`
del seeder; el name preserva casing original (`Python`, `Node.js`,
`AWS Lambda`).
"""

from sqlalchemy import (
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

import shared.db.models.taxonomy.catalog  # noqa: F401 -- FK target (catalog)

from ...base import Base, TimestampMixin, UUIDPKMixin
from ...enums import skill_kind_enum


class Skill(UUIDPKMixin, TimestampMixin, Base):
    """Competencia deduplicada (el string `'TypeScript'` es UNA fila).

    `slug` UK (clave canonica para URLs estables), `name` display.
    """

    __tablename__ = 'cv_skills'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)


class SkillCategory(UUIDPKMixin, TimestampMixin, Base):
    """Categoria de skills (agrupa skills por dominio)."""

    __tablename__ = 'cv_skill_categories'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    kind: Mapped[str] = mapped_column(skill_kind_enum, nullable=False)


class SkillCategorySkill(Base):
    """Categoria de skills <-> skill. `position` preserva el orden."""

    __tablename__ = 'cv_skill_category_skills'

    skill_category_id: Mapped[str] = mapped_column(
        ForeignKey('cv_skill_categories.id', ondelete='CASCADE'),
        nullable=False,
    )
    skill_id: Mapped[str] = mapped_column(
        ForeignKey('cv_skills.id', ondelete='CASCADE'), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (PrimaryKeyConstraint('skill_category_id', 'skill_id'),)


class SkillCategoryNiche(Base):
    """Union skill_category <-> niche."""

    __tablename__ = 'cv_skill_category_niches'

    skill_category_id: Mapped[str] = mapped_column(
        ForeignKey('cv_skill_categories.id', ondelete='CASCADE'),
        nullable=False,
    )
    niche_id: Mapped[str] = mapped_column(
        ForeignKey('tax_niches.id', ondelete='CASCADE'), nullable=False
    )

    __table_args__ = (PrimaryKeyConstraint('skill_category_id', 'niche_id'),)
