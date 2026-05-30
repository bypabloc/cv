"""@module cv.education — formacion academica + junction con niches."""

from datetime import date

from sqlalchemy import Date, ForeignKey, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

import shared.db.models.taxonomy.catalog  # noqa: F401 -- FK target (catalog)

from ...base import Base, TimestampMixin, UUIDPKMixin


class EducationEntry(UUIDPKMixin, TimestampMixin, Base):
    """Una entrada de formacion academica.

    Renombrado de `Education` a `EducationEntry` (la tabla es
    `cv_education_entries`, plural natural de un non-count noun).

    Fechas como `DATE` (post-rename, antes era VARCHAR(16)).
    """

    __tablename__ = 'cv_education_entries'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    institution: Mapped[str] = mapped_column(String(200), nullable=False)
    started_on: Mapped[date] = mapped_column(Date, nullable=False)
    ended_on: Mapped[date | None] = mapped_column(Date)
    url: Mapped[str | None] = mapped_column(String(500))


class EducationEntryNiche(Base):
    """Union education_entry <-> niche."""

    __tablename__ = 'cv_education_entry_niches'

    education_entry_id: Mapped[str] = mapped_column(
        ForeignKey('cv_education_entries.id', ondelete='CASCADE'),
        nullable=False,
    )
    niche_id: Mapped[str] = mapped_column(
        ForeignKey('tax_niches.id', ondelete='CASCADE'), nullable=False
    )

    __table_args__ = (PrimaryKeyConstraint('education_entry_id', 'niche_id'),)
