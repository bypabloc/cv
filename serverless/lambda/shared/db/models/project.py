"""@module project — proyectos + case study detallado + metricas.

`projects` modela cada proyecto. Textos bilingues (`summary`, `description`,
`case_study`) -> `translations`. El `stack[]` se normaliza via la union
`project_tech_tags` al catalogo `tech_tags`.

Estructuras embebidas del YAML:
- `caseStudyDetailed` (problem/process/result, bilingue) -> tabla 1:1
  `project_case_studies` + textos en `translations`.
- `metrics` ({market, product, ...} con claves variables) -> tabla 1:N
  `project_metrics` (par clave/valor ordenado).
"""

from typing import Any

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin, UUIDPKMixin
from ..enums import project_status_enum, project_type_enum


class Project(UUIDPKMixin, TimestampMixin, Base):
    """Un proyecto del CV.

    Textos bilingues en `translations` (entity_type='project'): `name` NO es
    bilingue (es un nombre propio) y queda como columna; `summary`,
    `description`, `case_study` SI son bilingues -> `translations`.
    Niches via `project_niches`; priority via `niche_priorities`.
    """

    __tablename__ = 'projects'

    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    # Nombre propio del proyecto — NO bilingue.
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500))
    # Links adicionales del proyecto (sitios alternos en produccion). JSONB
    # con shape `[{"label": {"es": "X", "en": "X"}, "url": "https://..."}, ...]`.
    # Si el proyecto solo tiene 1 URL en produccion, se queda en `url`; este
    # campo solo aparece cuando hay >1 sitios alternos (ej. el sistema de
    # saldar deudas Chile cubre 3 marcas).
    links: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    repo: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(project_status_enum, nullable=False)
    project_type: Mapped[str] = mapped_column(project_type_enum, nullable=False)
    is_confidential: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    # Marcador interno: la entry tiene metricas estimadas sin validar.
    metrics_estimated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )


class ProjectCaseStudy(UUIDPKMixin, TimestampMixin, Base):
    """Case study detallado de un proyecto (relacion 1:1).

    `problem` / `process` / `result` son bilingues -> `translations`
    (entity_type='project_case_study'). Esta tabla solo enlaza al proyecto;
    los textos viven en `translations`.
    """

    __tablename__ = 'project_case_studies'

    project_id: Mapped[str] = mapped_column(
        ForeignKey('projects.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
    )


class ProjectMetric(UUIDPKMixin, TimestampMixin, Base):
    """Una metrica de un proyecto (par clave/valor ordenado).

    El YAML `metrics` tiene claves variables ({market, product,
    architecture, ...}); cada par es una fila. `metric_value` NO es
    bilingue en la data actual (valores tipo "México", nombres tecnicos).
    """

    __tablename__ = 'project_metrics'

    project_id: Mapped[str] = mapped_column(
        ForeignKey('projects.id', ondelete='CASCADE'),
        nullable=False,
    )
    metric_key: Mapped[str] = mapped_column(String(80), nullable=False)
    metric_value: Mapped[str] = mapped_column(String(500), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        # Clave natural — habilita el upsert idempotente del seed.
        UniqueConstraint('project_id', 'metric_key', name='project_metric'),
    )
