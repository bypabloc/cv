"""@module cv.education — formacion academica + junction con niches."""

from sqlalchemy import ForeignKey, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base, TimestampMixin, UUIDPKMixin


class Education(UUIDPKMixin, TimestampMixin, Base):
    """Formacion academica.

    Textos bilingues en `translations` (entity_type='education'): `degree`
    (opcional), `description`. `start` / `end` son anios o 'Actual'/'Present'
    -> varchar.
    """

    __tablename__ = 'education'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    institution: Mapped[str] = mapped_column(String(200), nullable=False)
    start_year: Mapped[str] = mapped_column(String(16), nullable=False)
    end_year: Mapped[str] = mapped_column(String(16), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500))


class EducationNiche(Base):
    """Union education <-> niche."""

    __tablename__ = 'education_niches'

    education_id: Mapped[str] = mapped_column(
        ForeignKey('education.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = mapped_column(
        ForeignKey('niches.id', ondelete='CASCADE'), nullable=False
    )

    __table_args__ = (PrimaryKeyConstraint('education_id', 'niche_id'),)
