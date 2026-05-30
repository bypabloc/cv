"""@module cv.cv_entity — entidades CV simples + sus junctions.

Agrupa 5 entidades sin auxiliares 1:N propios:
- Award + AwardNiche                  (date `awarded_on`)
- Certificate + CertificateNiche      (date `issued_on`)
- Language + LanguageNiche
- Publication + PublicationNiche      (date `published_on`)
- Endorsement + EndorsementNiche      (ex `Reference` — renombrado porque
  `references` es palabra reservada SQL)

ENUM entity_type tras la migracion: `'reference'` -> `'endorsement'`.
"""

from datetime import date

from sqlalchemy import (
    Date,
    ForeignKey,
    PrimaryKeyConstraint,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

import shared.db.models.taxonomy.catalog  # noqa: F401 -- FK target (catalog)

from ...base import Base, TimestampMixin, UUIDPKMixin

# Awards -------------------------------------------------------------------


class Award(UUIDPKMixin, TimestampMixin, Base):
    """Premio o reconocimiento. `awarded_on` DATE (antes VARCHAR(7))."""

    __tablename__ = 'cv_awards'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    issuer: Mapped[str] = mapped_column(String(200), nullable=False)
    awarded_on: Mapped[date] = mapped_column(Date, nullable=False)
    url: Mapped[str | None] = mapped_column(String(500))


class AwardNiche(Base):
    """Union award <-> niche."""

    __tablename__ = 'cv_award_niches'

    award_id: Mapped[str] = mapped_column(
        ForeignKey('cv_awards.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = mapped_column(
        ForeignKey('tax_niches.id', ondelete='CASCADE'), nullable=False
    )

    __table_args__ = (PrimaryKeyConstraint('award_id', 'niche_id'),)


# Certificates -------------------------------------------------------------


class Certificate(UUIDPKMixin, TimestampMixin, Base):
    """Certificacion tecnica."""

    __tablename__ = 'cv_certificates'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    issuer: Mapped[str] = mapped_column(String(200), nullable=False)
    issued_on: Mapped[date] = mapped_column(Date, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)


class CertificateNiche(Base):
    """Union certificate <-> niche."""

    __tablename__ = 'cv_certificate_niches'

    certificate_id: Mapped[str] = mapped_column(
        ForeignKey('cv_certificates.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = mapped_column(
        ForeignKey('tax_niches.id', ondelete='CASCADE'), nullable=False
    )

    __table_args__ = (PrimaryKeyConstraint('certificate_id', 'niche_id'),)


# Languages ----------------------------------------------------------------


class Language(UUIDPKMixin, TimestampMixin, Base):
    """Idioma hablado + nivel."""

    __tablename__ = 'cv_languages'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)


class LanguageNiche(Base):
    """Union language <-> niche."""

    __tablename__ = 'cv_language_niches'

    language_id: Mapped[str] = mapped_column(
        ForeignKey('cv_languages.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = mapped_column(
        ForeignKey('tax_niches.id', ondelete='CASCADE'), nullable=False
    )

    __table_args__ = (PrimaryKeyConstraint('language_id', 'niche_id'),)


# Publications -------------------------------------------------------------


class Publication(UUIDPKMixin, TimestampMixin, Base):
    """Articulo / publicacion."""

    __tablename__ = 'cv_publications'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    platform: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    canonical_url: Mapped[str | None] = mapped_column(String(500))
    published_on: Mapped[date] = mapped_column(Date, nullable=False)


class PublicationNiche(Base):
    """Union publication <-> niche."""

    __tablename__ = 'cv_publication_niches'

    publication_id: Mapped[str] = mapped_column(
        ForeignKey('cv_publications.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = mapped_column(
        ForeignKey('tax_niches.id', ondelete='CASCADE'), nullable=False
    )

    __table_args__ = (PrimaryKeyConstraint('publication_id', 'niche_id'),)


# Endorsements (ex References) --------------------------------------------


class Endorsement(UUIDPKMixin, TimestampMixin, Base):
    """Recomendacion profesional. Renombrado de `Reference`.

    La tabla es `cv_endorsements` porque `references` es palabra
    reservada SQL (clausula FK). ENUM entity_type: 'endorsement'.
    """

    __tablename__ = 'cv_endorsements'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[str | None] = mapped_column(String(200))
    linkedin_url: Mapped[str] = mapped_column(String(500), nullable=False)


class EndorsementNiche(Base):
    """Union endorsement <-> niche. FK column: `endorsement_id`."""

    __tablename__ = 'cv_endorsement_niches'

    endorsement_id: Mapped[str] = mapped_column(
        ForeignKey('cv_endorsements.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = mapped_column(
        ForeignKey('tax_niches.id', ondelete='CASCADE'), nullable=False
    )

    __table_args__ = (PrimaryKeyConstraint('endorsement_id', 'niche_id'),)
