"""@module catalog — vocabularios compartidos del CV.

Tres catalogos deduplicados que el resto del schema referencia via FK:

- `niches`            — los 5 nichos del portfolio (seed fijo).
- `skills`            — competencias deduplicadas. Unifica los strings de
                        `skill_categories.skills[]` y de
                        `experience.skillsTechnical/skillsSoft`.
- `tech_tags`         — stack tecnico deduplicado (el `stack[]` de projects).
                        Separado de `skills`: su semantica es distinta
                        (stack de un proyecto vs competencia declarada).
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin, UUIDPKMixin


class Niche(UUIDPKMixin, TimestampMixin, Base):
    """Catalogo de los 5 nichos del portfolio. Seed fijo e inmutable."""

    __tablename__ = 'niches'

    # 'fintech' | 'architect' | 'leader' | 'vibe' | 'generic'
    slug: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    # Orden de presentacion canonico del nicho.
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Skill(UUIDPKMixin, TimestampMixin, Base):
    """Competencia deduplicada. El string `'TypeScript'` que aparece en N
    YAML distintos es UNA fila aqui (`name` UNIQUE).
    """

    __tablename__ = 'skills'

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)


class TechTag(UUIDPKMixin, TimestampMixin, Base):
    """Etiqueta de stack tecnico deduplicada (el `stack[]` de un proyecto)."""

    __tablename__ = 'tech_tags'

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
