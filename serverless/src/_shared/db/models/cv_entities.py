"""@module cv_entities — entidades del CV de estructura simple.

Agrupa las 7 entidades sin sub-tablas propias: certificates, awards,
education, references, languages, skill_categories, publications.

Patron comun: PK uuid + `slug` UNIQUE. Textos bilingues -> `translations`;
niches -> `<entidad>_niches`; priority -> `niche_priorities` (cuando aplica).
"""

from sqlalchemy import CheckConstraint, Date, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin, UUIDPKMixin
from ..enums import skill_kind_enum

# Regex YYYY-MM (mismo formato que experience.start_ym).
_YM_RE = r'^\d{4}-(0[1-9]|1[0-2])$'


class Certificate(UUIDPKMixin, TimestampMixin, Base):
    """Certificacion tecnica.

    `title` e `issuer` NO son bilingues en la data actual (nombres propios).
    `date` es YYYY-MM-DD -> columna `date` nativa.
    """

    __tablename__ = 'certificates'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    issuer: Mapped[str] = mapped_column(String(200), nullable=False)
    issued_on: Mapped[Date] = mapped_column(Date, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)


class Award(UUIDPKMixin, TimestampMixin, Base):
    """Premio o reconocimiento.

    Textos bilingues en `translations` (entity_type='award'): `title`,
    `motivation`. `date` es YYYY-MM -> varchar(7).
    """

    __tablename__ = 'awards'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    issuer: Mapped[str] = mapped_column(String(200), nullable=False)
    awarded_ym: Mapped[str] = mapped_column(String(7), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500))

    __table_args__ = (
        CheckConstraint(f"awarded_ym ~ '{_YM_RE}'", name='awarded_ym_format'),
    )


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


class Reference(UUIDPKMixin, TimestampMixin, Base):
    """Referencia profesional.

    Texto bilingue en `translations` (entity_type='reference'): `relation`.
    `name` y `role` son datos propios -> columnas.
    """

    __tablename__ = 'references'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[str | None] = mapped_column(String(200))
    linkedin_url: Mapped[str] = mapped_column(String(500), nullable=False)


class Language(UUIDPKMixin, TimestampMixin, Base):
    """Idioma hablado + nivel.

    Textos bilingues en `translations` (entity_type='language'): `name`,
    `level`. El `slug` es opcional en el YAML; aqui se exige (clave natural).
    """

    __tablename__ = 'languages'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)


class SkillCategory(UUIDPKMixin, TimestampMixin, Base):
    """Categoria de skills (agrupa skills por dominio).

    Texto bilingue en `translations` (entity_type='skill_category'): `name`.
    Las skills se enlazan via `skill_category_skills` al catalogo `skills`.
    """

    __tablename__ = 'skill_categories'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    kind: Mapped[str] = mapped_column(skill_kind_enum, nullable=False)


class Publication(UUIDPKMixin, TimestampMixin, Base):
    """Articulo / publicacion (ej. Medium). La coleccion esta vacia hoy en
    los YAML, pero el schema existe en Zod — se modela por completitud.

    Texto bilingue en `translations` (entity_type='publication'): `summary`.
    `title` y `platform` son datos propios. `date` es YYYY-MM-DD.
    """

    __tablename__ = 'publications'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    platform: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    canonical_url: Mapped[str | None] = mapped_column(String(500))
    published_on: Mapped[Date] = mapped_column(Date, nullable=False)
