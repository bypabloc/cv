"""@module cv.cv_entity — entidades CV simples + sus junctions.

Agrupa las 5 entidades sin auxiliares 1:N propios:
- Award + AwardNiche
- Certificate + CertificateNiche
- Language + LanguageNiche
- Publication + PublicationNiche
- Reference + ReferenceNiche

Patron comun: PK uuid + `slug` UNIQUE + junction `<entidad>_niches`.
Textos bilingues -> `translations`; priority -> `niche_priorities`.
"""

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    PrimaryKeyConstraint,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base, TimestampMixin, UUIDPKMixin

# Regex YYYY-MM (mismo formato que experience.start_ym).
_YM_RE = r'^\d{4}-(0[1-9]|1[0-2])$'


# Awards -------------------------------------------------------------------

class Award(UUIDPKMixin, TimestampMixin, Base):
    """Premio o reconocimiento."""

    __tablename__ = 'awards'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    issuer: Mapped[str] = mapped_column(String(200), nullable=False)
    awarded_ym: Mapped[str] = mapped_column(String(7), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500))

    __table_args__ = (
        CheckConstraint(f"awarded_ym ~ '{_YM_RE}'", name='awarded_ym_format'),
    )


class AwardNiche(Base):
    """Union award <-> niche."""

    __tablename__ = 'award_niches'

    award_id: Mapped[str] = mapped_column(
        ForeignKey('awards.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = mapped_column(
        ForeignKey('niches.id', ondelete='CASCADE'), nullable=False
    )

    __table_args__ = (PrimaryKeyConstraint('award_id', 'niche_id'),)


# Certificates -------------------------------------------------------------

class Certificate(UUIDPKMixin, TimestampMixin, Base):
    """Certificacion tecnica."""

    __tablename__ = 'certificates'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    issuer: Mapped[str] = mapped_column(String(200), nullable=False)
    issued_on: Mapped[Date] = mapped_column(Date, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)


class CertificateNiche(Base):
    """Union certificate <-> niche."""

    __tablename__ = 'certificate_niches'

    certificate_id: Mapped[str] = mapped_column(
        ForeignKey('certificates.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = mapped_column(
        ForeignKey('niches.id', ondelete='CASCADE'), nullable=False
    )

    __table_args__ = (PrimaryKeyConstraint('certificate_id', 'niche_id'),)


# Languages ----------------------------------------------------------------

class Language(UUIDPKMixin, TimestampMixin, Base):
    """Idioma hablado + nivel.

    Textos bilingues en `translations` (entity_type='language'): `name`,
    `level`.
    """

    __tablename__ = 'languages'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)


class LanguageNiche(Base):
    """Union language <-> niche."""

    __tablename__ = 'language_niches'

    language_id: Mapped[str] = mapped_column(
        ForeignKey('languages.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = mapped_column(
        ForeignKey('niches.id', ondelete='CASCADE'), nullable=False
    )

    __table_args__ = (PrimaryKeyConstraint('language_id', 'niche_id'),)


# Publications -------------------------------------------------------------

class Publication(UUIDPKMixin, TimestampMixin, Base):
    """Articulo / publicacion."""

    __tablename__ = 'publications'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    platform: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    canonical_url: Mapped[str | None] = mapped_column(String(500))
    published_on: Mapped[Date] = mapped_column(Date, nullable=False)


class PublicationNiche(Base):
    """Union publication <-> niche."""

    __tablename__ = 'publication_niches'

    publication_id: Mapped[str] = mapped_column(
        ForeignKey('publications.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = mapped_column(
        ForeignKey('niches.id', ondelete='CASCADE'), nullable=False
    )

    __table_args__ = (PrimaryKeyConstraint('publication_id', 'niche_id'),)


# References ---------------------------------------------------------------

class Reference(UUIDPKMixin, TimestampMixin, Base):
    """Referencia profesional."""

    __tablename__ = 'references'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[str | None] = mapped_column(String(200))
    linkedin_url: Mapped[str] = mapped_column(String(500), nullable=False)


class ReferenceNiche(Base):
    """Union reference <-> niche."""

    __tablename__ = 'reference_niches'

    reference_id: Mapped[str] = mapped_column(
        ForeignKey('references.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = mapped_column(
        ForeignKey('niches.id', ondelete='CASCADE'), nullable=False
    )

    __table_args__ = (PrimaryKeyConstraint('reference_id', 'niche_id'),)
