"""@module cv.experience — experiencias laborales + bullets + junctions."""

from datetime import date

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

import shared.db.models.cv.skill
import shared.db.models.taxonomy.catalog  # noqa: F401 -- FK target (catalog)

from ...base import Base, TimestampMixin, UUIDPKMixin
from ...enums import bullet_kind_enum, seniority_enum, skill_kind_enum


class Experience(UUIDPKMixin, TimestampMixin, Base):
    """Una experiencia laboral (un puesto).

    Fechas como `DATE` (post-rename, antes era VARCHAR(7) YYYY-MM).
    El seeder convierte `'2024-01'` del YAML a `date(2024, 1, 1)`.
    """

    __tablename__ = 'cv_experiences'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    company: Mapped[str] = mapped_column(String(160), nullable=False)
    country: Mapped[str] = mapped_column(String(120), nullable=False)
    company_url: Mapped[str | None] = mapped_column(String(500))
    started_on: Mapped[date] = mapped_column(Date, nullable=False)
    ended_on: Mapped[date | None] = mapped_column(Date)
    seniority: Mapped[str] = mapped_column(seniority_enum, nullable=False)
    metrics_estimated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )


class ExperienceBullet(UUIDPKMixin, TimestampMixin, Base):
    """Un bullet de una experiencia (responsabilidad o logro)."""

    __tablename__ = 'cv_experience_bullets'

    experience_id: Mapped[str] = mapped_column(
        ForeignKey('cv_experiences.id', ondelete='CASCADE'),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(bullet_kind_enum, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint(
            'experience_id', 'kind', 'position', name='experience_bullet'
        ),
    )


class ExperienceNiche(Base):
    """Union experience <-> niche."""

    __tablename__ = 'cv_experience_niches'

    experience_id: Mapped[str] = mapped_column(
        ForeignKey('cv_experiences.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = mapped_column(
        ForeignKey('tax_niches.id', ondelete='CASCADE'), nullable=False
    )

    __table_args__ = (PrimaryKeyConstraint('experience_id', 'niche_id'),)


class ExperienceSkill(Base):
    """Experiencia <-> skill."""

    __tablename__ = 'cv_experience_skills'

    experience_id: Mapped[str] = mapped_column(
        ForeignKey('cv_experiences.id', ondelete='CASCADE'), nullable=False
    )
    skill_id: Mapped[str] = mapped_column(
        ForeignKey('cv_skills.id', ondelete='CASCADE'), nullable=False
    )
    kind: Mapped[str] = mapped_column(skill_kind_enum, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('experience_id', 'skill_id', 'kind'),
    )
