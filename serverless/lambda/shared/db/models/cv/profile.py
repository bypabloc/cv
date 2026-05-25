"""@module cv.profile — singleton de perfil + stats + junction con niches."""

from sqlalchemy import ForeignKey, Integer, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base, TimestampMixin, UUIDPKMixin


class Profile(UUIDPKMixin, TimestampMixin, Base):
    """Perfil de la persona del CV. Singleton (1 fila)."""

    __tablename__ = 'cv_profiles'

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    handle: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    location: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40))
    linkedin_url: Mapped[str] = mapped_column(String(500), nullable=False)
    github_url: Mapped[str] = mapped_column(String(500), nullable=False)
    website_url: Mapped[str | None] = mapped_column(String(500))
    avatar_url: Mapped[str] = mapped_column(String(500), nullable=False)


class ProfileStats(UUIDPKMixin, TimestampMixin, Base):
    """Stats declarados del perfil. Relacion 1:1 con `cv_profiles`."""

    __tablename__ = 'cv_profile_stats'

    profile_id: Mapped[str] = mapped_column(
        ForeignKey('cv_profiles.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
    )
    years_experience: Mapped[int] = mapped_column(Integer, nullable=False)
    companies: Mapped[int] = mapped_column(Integer, nullable=False)
    countries: Mapped[int] = mapped_column(Integer, nullable=False)
    certifications: Mapped[int] = mapped_column(Integer, nullable=False)


class ProfileNiche(Base):
    """Union profile <-> niche."""

    __tablename__ = 'cv_profile_niches'

    profile_id: Mapped[str] = mapped_column(
        ForeignKey('cv_profiles.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = mapped_column(
        ForeignKey('tax_niches.id', ondelete='CASCADE'), nullable=False
    )

    __table_args__ = (PrimaryKeyConstraint('profile_id', 'niche_id'),)
