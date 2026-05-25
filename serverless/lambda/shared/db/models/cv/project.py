"""@module cv.project — proyectos + case study + metricas + junctions."""

from typing import Any

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base, TimestampMixin, UUIDPKMixin
from ...enums import project_status_enum, project_type_enum


class Project(UUIDPKMixin, TimestampMixin, Base):
    """Un proyecto del CV."""

    __tablename__ = 'cv_projects'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500))
    links: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    repo: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(project_status_enum, nullable=False)
    project_type: Mapped[str] = mapped_column(project_type_enum, nullable=False)
    is_confidential: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    metrics_estimated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )


class ProjectCaseStudy(UUIDPKMixin, TimestampMixin, Base):
    """Case study detallado de un proyecto (relacion 1:1)."""

    __tablename__ = 'cv_project_case_studies'

    project_id: Mapped[str] = mapped_column(
        ForeignKey('cv_projects.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
    )


class ProjectMetric(UUIDPKMixin, TimestampMixin, Base):
    """Una metrica de un proyecto (par clave/valor ordenado)."""

    __tablename__ = 'cv_project_metrics'

    project_id: Mapped[str] = mapped_column(
        ForeignKey('cv_projects.id', ondelete='CASCADE'),
        nullable=False,
    )
    metric_key: Mapped[str] = mapped_column(String(80), nullable=False)
    metric_value: Mapped[str] = mapped_column(String(500), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint('project_id', 'metric_key', name='project_metric'),
    )


class ProjectNiche(Base):
    """Union project <-> niche."""

    __tablename__ = 'cv_project_niches'

    project_id: Mapped[str] = mapped_column(
        ForeignKey('cv_projects.id', ondelete='CASCADE'), nullable=False
    )
    niche_id: Mapped[str] = mapped_column(
        ForeignKey('tax_niches.id', ondelete='CASCADE'), nullable=False
    )

    __table_args__ = (PrimaryKeyConstraint('project_id', 'niche_id'),)


class ProjectTechTag(Base):
    """Proyecto <-> tech tag (el `stack[]`)."""

    __tablename__ = 'cv_project_tech_tags'

    project_id: Mapped[str] = mapped_column(
        ForeignKey('cv_projects.id', ondelete='CASCADE'), nullable=False
    )
    tech_tag_id: Mapped[str] = mapped_column(
        ForeignKey('tax_tech_tags.id', ondelete='CASCADE'), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (PrimaryKeyConstraint('project_id', 'tech_tag_id'),)
