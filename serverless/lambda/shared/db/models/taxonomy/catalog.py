"""@module taxonomy.catalog — catalogos compartidos no-CV-especificos.

- `tax_niches`    — los 5 nichos del portfolio (seed fijo).
- `tax_tech_tags` — stack tecnico deduplicado (slug + name).
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base, TimestampMixin, UUIDPKMixin


class Niche(UUIDPKMixin, TimestampMixin, Base):
    """Catalogo de los 5 nichos del portfolio."""

    __tablename__ = 'tax_niches'

    slug: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    display_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )


class TechTag(UUIDPKMixin, TimestampMixin, Base):
    """Etiqueta de stack tecnico deduplicada (slug UK + name display)."""

    __tablename__ = 'tax_tech_tags'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
