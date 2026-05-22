"""@module experience — experiencias laborales + sus bullets.

`experiences` modela cada puesto. Textos bilingues (`role`) -> `translations`.
Las listas `responsibilities[]` / `achievements[]` (ordenadas y bilingues) se
modelan como `experience_bullets` (1 fila por bullet) + sus textos en
`translations` (entity_type='experience_bullet').

Las skills (`skillsTechnical` + `skillsSoft`) se enlazan via la union
`experience_skills` al catalogo `skills`; el flag tecnica/blanda vive en la
fila de union.
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin, UUIDPKMixin
from ..enums import bullet_kind_enum, seniority_enum

# Regex YYYY-MM: el dato del CV no es una fecha completa, se valida con CHECK.
_YM_RE = r'^\d{4}-(0[1-9]|1[0-2])$'


class Experience(UUIDPKMixin, TimestampMixin, Base):
    """Una experiencia laboral (un puesto).

    Texto bilingue en `translations` (entity_type='experience'): `role`.
    Niches via `experience_niches`; priority via `niche_priorities`.
    """

    __tablename__ = 'experiences'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    company: Mapped[str] = mapped_column(String(160), nullable=False)
    # Pais donde se desempeño el rol (ej. "Venezuela", "Perú", "Chile").
    country: Mapped[str] = mapped_column(String(120), nullable=False)
    company_url: Mapped[str | None] = mapped_column(String(500))
    # YYYY-MM. varchar + CHECK: el dato del CV no es fecha completa.
    start_ym: Mapped[str] = mapped_column(String(7), nullable=False)
    end_ym: Mapped[str | None] = mapped_column(String(7))
    seniority: Mapped[str] = mapped_column(seniority_enum, nullable=False)
    # Marcador interno: la entry tiene metricas estimadas sin validar.
    metrics_estimated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    __table_args__ = (
        # start siempre bien formado; end opcional, pero si esta presente
        # tambien debe ser YYYY-MM.
        CheckConstraint(f"start_ym ~ '{_YM_RE}'", name='start_ym_format'),
        CheckConstraint(
            f"end_ym IS NULL OR end_ym ~ '{_YM_RE}'",
            name='end_ym_format',
        ),
        {'comment': 'Experiencias laborales del CV'},
    )


class ExperienceBullet(UUIDPKMixin, TimestampMixin, Base):
    """Un bullet de una experiencia (responsabilidad o logro).

    El texto bilingue del bullet vive en `translations`
    (entity_type='experience_bullet', field='text'). `position` preserva
    el orden original del YAML.
    """

    __tablename__ = 'experience_bullets'

    experience_id: Mapped[str] = mapped_column(
        ForeignKey('experiences.id', ondelete='CASCADE'),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(bullet_kind_enum, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        # Clave natural del bullet — habilita el upsert idempotente del seed.
        UniqueConstraint(
            'experience_id', 'kind', 'position', name='experience_bullet'
        ),
    )
