"""@module profile — singleton de perfil + sus stats.

`profile` es un singleton (siempre 1 fila). Sus textos bilingues
(`headline`, `summary`, `availability`) NO viven aqui: van a `translations`.
Los campos no-bilingues (contactos, urls) son columnas nativas.
"""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin, UUIDPKMixin


class Profile(UUIDPKMixin, TimestampMixin, Base):
    """Perfil de la persona del CV. Singleton (1 fila).

    Textos bilingues en `translations` (entity_type='profile'):
    `headline`, `summary`, `availability`.
    """

    __tablename__ = 'profile'

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    handle: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    # Ciudad y pais en formato limpio (ej. "Lima, Perú").
    location: Mapped[str] = mapped_column(String(160), nullable=False)
    # Contactos.
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40))
    linkedin_url: Mapped[str] = mapped_column(String(500), nullable=False)
    github_url: Mapped[str] = mapped_column(String(500), nullable=False)
    website_url: Mapped[str | None] = mapped_column(String(500))
    avatar_url: Mapped[str] = mapped_column(String(500), nullable=False)


class ProfileStats(UUIDPKMixin, TimestampMixin, Base):
    """Stats declarados del perfil (cards de la StatsBar). Relacion 1:1
    con `profile` — se separa porque es un grupo cohesivo opcional.
    """

    __tablename__ = 'profile_stats'

    profile_id: Mapped[str] = mapped_column(
        ForeignKey('profile.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
    )
    years_experience: Mapped[int] = mapped_column(Integer, nullable=False)
    companies: Mapped[int] = mapped_column(Integer, nullable=False)
    countries: Mapped[int] = mapped_column(Integer, nullable=False)
    certifications: Mapped[int] = mapped_column(Integer, nullable=False)
