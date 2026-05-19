"""@module junctions — tablas de union N:M del schema del CV.

Dos familias:

1. `<entidad>_niches` — enlaza cada entidad con sus nichos. Union PURA
   `(entity_id, niche_id)` con PK compuesta. El priority NO vive aqui
   (decision del usuario): va en `niche_priorities` (translations.py).

2. Uniones de vocabulario:
   - `experience_skills` — experiencia <-> skill, con `kind` (technical/soft)
     en la fila de union (una skill puede ser tecnica en un rol).
   - `skill_category_skills` — categoria de skills <-> skill (union pura).
   - `project_tech_tags` — proyecto <-> tech tag (union pura).
"""

from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .base import Base
from .enums import skill_kind_enum


def _niche_fk() -> Mapped[str]:
    """FK a `niches.id`. Helper para no repetir la definicion en cada union."""
    return mapped_column(
        ForeignKey('niches.id', ondelete='CASCADE'), nullable=False
    )


# --------------------------------------------------------------------------
# Familia 1: <entidad>_niches — uniones puras entidad <-> niche.
# Una clase por entidad filtrable por nicho. PK compuesta.
# --------------------------------------------------------------------------


class ExperienceNiche(Base):
    __tablename__ = 'experience_niches'

    experience_id: Mapped[str] = mapped_column(
        ForeignKey('experiences.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = _niche_fk()

    __table_args__ = (PrimaryKeyConstraint('experience_id', 'niche_id'),)


class ProjectNiche(Base):
    __tablename__ = 'project_niches'

    project_id: Mapped[str] = mapped_column(
        ForeignKey('projects.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = _niche_fk()

    __table_args__ = (PrimaryKeyConstraint('project_id', 'niche_id'),)


class CertificateNiche(Base):
    __tablename__ = 'certificate_niches'

    certificate_id: Mapped[str] = mapped_column(
        ForeignKey('certificates.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = _niche_fk()

    __table_args__ = (PrimaryKeyConstraint('certificate_id', 'niche_id'),)


class AwardNiche(Base):
    __tablename__ = 'award_niches'

    award_id: Mapped[str] = mapped_column(
        ForeignKey('awards.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = _niche_fk()

    __table_args__ = (PrimaryKeyConstraint('award_id', 'niche_id'),)


class EducationNiche(Base):
    __tablename__ = 'education_niches'

    education_id: Mapped[str] = mapped_column(
        ForeignKey('education.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = _niche_fk()

    __table_args__ = (PrimaryKeyConstraint('education_id', 'niche_id'),)


class ReferenceNiche(Base):
    __tablename__ = 'reference_niches'

    reference_id: Mapped[str] = mapped_column(
        ForeignKey('references.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = _niche_fk()

    __table_args__ = (PrimaryKeyConstraint('reference_id', 'niche_id'),)


class LanguageNiche(Base):
    __tablename__ = 'language_niches'

    language_id: Mapped[str] = mapped_column(
        ForeignKey('languages.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = _niche_fk()

    __table_args__ = (PrimaryKeyConstraint('language_id', 'niche_id'),)


class PublicationNiche(Base):
    __tablename__ = 'publication_niches'

    publication_id: Mapped[str] = mapped_column(
        ForeignKey('publications.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = _niche_fk()

    __table_args__ = (PrimaryKeyConstraint('publication_id', 'niche_id'),)


class SkillCategoryNiche(Base):
    __tablename__ = 'skill_category_niches'

    skill_category_id: Mapped[str] = mapped_column(
        ForeignKey('skill_categories.id', ondelete='CASCADE'),
        nullable=False,
    )
    niche_id: Mapped[str] = _niche_fk()

    __table_args__ = (PrimaryKeyConstraint('skill_category_id', 'niche_id'),)


# --------------------------------------------------------------------------
# Familia 2: uniones de vocabulario (skills / tech_tags).
# --------------------------------------------------------------------------


class ExperienceSkill(Base):
    """Experiencia <-> skill. `kind` en la fila de union: la misma skill
    puede declararse como tecnica en un rol y blanda en otro.
    """

    __tablename__ = 'experience_skills'

    experience_id: Mapped[str] = mapped_column(
        ForeignKey('experiences.id', ondelete='CASCADE'), nullable=False
    )
    skill_id: Mapped[str] = mapped_column(
        ForeignKey('skills.id', ondelete='CASCADE'), nullable=False
    )
    kind: Mapped[str] = mapped_column(skill_kind_enum, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('experience_id', 'skill_id', 'kind'),
    )


class SkillCategorySkill(Base):
    """Categoria de skills <-> skill. Union pura; `position` preserva el
    orden del array `skills[]` del YAML.
    """

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


class ProjectTechTag(Base):
    """Proyecto <-> tech tag (el `stack[]`). Union pura; `position`
    preserva el orden del array.
    """

    __tablename__ = 'project_tech_tags'

    project_id: Mapped[str] = mapped_column(
        ForeignKey('projects.id', ondelete='CASCADE'), nullable=False
    )
    tech_tag_id: Mapped[str] = mapped_column(
        ForeignKey('tech_tags.id', ondelete='CASCADE'), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (PrimaryKeyConstraint('project_id', 'tech_tag_id'),)
