"""@module cv.skill — catalogo skill + categoria + junctions.

`Skill` es el catalogo deduplicado de competencias. Se usa desde
`experience_skills` y `skill_category_skills`. Vive en `cv/` (no en
taxonomy/) porque su semantica es del CV — no es taxonomia global.
"""

from sqlalchemy import (
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base, TimestampMixin, UUIDPKMixin
from ...enums import skill_kind_enum


class Skill(UUIDPKMixin, TimestampMixin, Base):
    """Competencia deduplicada (el string `'TypeScript'` es UNA fila)."""

    __tablename__ = 'skills'

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)


class SkillCategory(UUIDPKMixin, TimestampMixin, Base):
    """Categoria de skills (agrupa skills por dominio).

    Texto bilingue en `translations` (entity_type='skill_category'): `name`.
    """

    __tablename__ = 'skill_categories'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    kind: Mapped[str] = mapped_column(skill_kind_enum, nullable=False)


class SkillCategorySkill(Base):
    """Categoria de skills <-> skill. `position` preserva el orden."""

    __tablename__ = 'skill_category_skills'

    skill_category_id: Mapped[str] = mapped_column(
        ForeignKey('skill_categories.id', ondelete='CASCADE'),
        nullable=False,
    )
    skill_id: Mapped[str] = mapped_column(
        ForeignKey('skills.id', ondelete='CASCADE'), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (PrimaryKeyConstraint('skill_category_id', 'skill_id'),)


class SkillCategoryNiche(Base):
    """Union skill_category <-> niche."""

    __tablename__ = 'skill_category_niches'

    skill_category_id: Mapped[str] = mapped_column(
        ForeignKey('skill_categories.id', ondelete='CASCADE'),
        nullable=False,
    )
    niche_id: Mapped[str] = mapped_column(
        ForeignKey('niches.id', ondelete='CASCADE'), nullable=False
    )

    __table_args__ = (PrimaryKeyConstraint('skill_category_id', 'niche_id'),)
