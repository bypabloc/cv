"""@module enums — ENUMs nativos PostgreSQL del schema del CV.

Cada enum se declara con `native_enum=True` para que Alembic lo cree como
tipo `CREATE TYPE ... AS ENUM` real en PostgreSQL (no como `VARCHAR + CHECK`).
Los valores reflejan exactamente los del schema Zod de `@portfolio/content`.
"""

from enum import StrEnum

from sqlalchemy import Enum as SAEnum


class Locale(StrEnum):
    """Idioma de una traduccion. Espeja los locales del frontend."""

    ES = 'es'
    EN = 'en'


class Seniority(StrEnum):
    """Seniority del rol de una experiencia (orden menor -> mayor)."""

    INTERN = 'intern'
    JUNIOR = 'junior'
    MID = 'mid'
    SENIOR = 'senior'
    LEAD = 'lead'


class ProjectType(StrEnum):
    """Categoria de un proyecto. Espeja `PROJECT_TYPES` de Zod."""

    WEB = 'web'
    MOBILE = 'mobile'
    CLI = 'cli'
    LIBRARY = 'library'
    AI = 'ai'
    FINTECH_PLATFORM = 'fintech-platform'


class ProjectStatus(StrEnum):
    """Estado de un proyecto."""

    ACTIVE = 'active'
    INACTIVE = 'inactive'
    CONCEPT = 'concept'


class SkillKind(StrEnum):
    """Tipo de categoria de skills."""

    TECHNICAL = 'technical'
    SOFT = 'soft'


class BulletKind(StrEnum):
    """Tipo de bullet de una experiencia."""

    RESPONSIBILITY = 'responsibility'
    ACHIEVEMENT = 'achievement'


class EntityType(StrEnum):
    """Tipo de entidad referenciada por las tablas polimorficas
    (`translations`, `niche_priorities`). Un valor por tabla de entidad
    cuyos textos o priority se modelan fuera de la propia tabla.
    """

    PROFILE = 'profile'
    EXPERIENCE = 'experience'
    EXPERIENCE_BULLET = 'experience_bullet'
    PROJECT = 'project'
    PROJECT_CASE_STUDY = 'project_case_study'
    PROJECT_METRIC = 'project_metric'
    SKILL_CATEGORY = 'skill_category'
    CERTIFICATE = 'certificate'
    AWARD = 'award'
    EDUCATION = 'education'
    REFERENCE = 'reference'  # rename a 'endorsement' en commit 4 (Alembic)
    LANGUAGE = 'language'
    PUBLICATION = 'publication'


# Instancias SAEnum reutilizables. SQLAlchemy lo deduplica por `name`, asi
# que se referencia el mismo objeto en todos los modelos.
#
# `values_callable`: por defecto SQLAlchemy persiste el NOMBRE del miembro
# del enum (`INTERN`), no su valor (`intern`). Con esta lambda PostgreSQL
# almacena el `.value` — que es lo que esperan el seed y el frontend.
_use_values = lambda e: [m.value for m in e]  # noqa: E731


def _enum(py_enum: type, name: str) -> SAEnum:
    """SAEnum nativo PostgreSQL que persiste el valor del miembro."""
    return SAEnum(
        py_enum,
        name=name,
        native_enum=True,
        values_callable=_use_values,
    )


locale_enum = _enum(Locale, 'locale')
seniority_enum = _enum(Seniority, 'seniority')
project_type_enum = _enum(ProjectType, 'project_type')
project_status_enum = _enum(ProjectStatus, 'project_status')
skill_kind_enum = _enum(SkillKind, 'skill_kind')
bullet_kind_enum = _enum(BulletKind, 'bullet_kind')
entity_type_enum = _enum(EntityType, 'entity_type')
