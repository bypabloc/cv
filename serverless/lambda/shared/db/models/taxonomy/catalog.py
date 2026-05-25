"""@module taxonomy.catalog — catalogos compartidos no-CV-especificos.

- `niches`    — los 5 nichos del portfolio (seed fijo).
- `tech_tags` — stack tecnico deduplicado.

`skills` vive en `cv/skill.py` (es del dominio CV, no taxonomia global).
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base, TimestampMixin, UUIDPKMixin


class Niche(UUIDPKMixin, TimestampMixin, Base):
    """Catalogo de los 5 nichos del portfolio."""

    __tablename__ = 'niches'

    slug: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class TechTag(UUIDPKMixin, TimestampMixin, Base):
    """Etiqueta de stack tecnico deduplicada."""

    __tablename__ = 'tech_tags'

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
