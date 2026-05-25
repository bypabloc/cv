"""Service de la operacion `cv`: lectura del CV desde Neon.

Orquestador delgado: delega en `shared.db.cv_repository` y normaliza
errores a `ServiceError`. El `core/` del Lambda `cv` NO importa
`sqlalchemy` directo — toda query del CV vive en `shared.db`.
"""

from __future__ import annotations

from typing import Any

from shared.db.cv_repository import (
    get_full_cv as _get_full_cv,
)
from shared.db.cv_repository import (
    get_profile as _get_profile,
)
from shared.db.cv_repository import (
    list_awards as _list_awards,
)
from shared.db.cv_repository import (
    list_certificates as _list_certificates,
)
from shared.db.cv_repository import (
    list_education as _list_education,
)
from shared.db.cv_repository import (
    list_experiences as _list_experiences,
)
from shared.db.cv_repository import (
    list_languages as _list_languages,
)
from shared.db.cv_repository import (
    list_projects as _list_projects,
)
from shared.db.cv_repository import (
    list_references as _list_references,
)
from shared.db.cv_repository import (
    list_skill_categories as _list_skill_categories,
)
from shared.db.repository import RepositoryError


class ServiceError(Exception):
    """Error de negocio del Lambda `cv`.

    El controller lo captura y lo traduce a la respuesta normalizada
    `{is_valid: False, data, code}`.
    """

    def __init__(
        self,
        message: str,
        *,
        code: int = 5000,
        error_code: str = 'SERVICE_ERROR',
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.error_code = error_code


def _wrap(fn: Any, **kwargs: Any) -> Any:
    """Ejecuta una funcion de cv_repository traduciendo errores."""
    try:
        return fn(**kwargs)
    except RepositoryError as exc:
        raise ServiceError(
            exc.message,
            code=exc.code,
            error_code=exc.error_code,
        ) from exc


def get_full_cv(*, niche: str | None, locale: str) -> dict[str, Any]:
    """Devuelve el CV completo (todas las colecciones)."""
    return _wrap(_get_full_cv, niche=niche, locale=locale)


def get_profile(*, locale: str) -> dict[str, Any]:
    """Devuelve el profile + stats + textos bilingues."""
    return _wrap(_get_profile, locale=locale)


def list_experiences(*, niche: str | None, locale: str) -> list[dict[str, Any]]:
    """Devuelve las experiencias filtradas por niche."""
    return _wrap(_list_experiences, niche=niche, locale=locale)


def list_projects(*, niche: str | None, locale: str) -> list[dict[str, Any]]:
    """Devuelve los proyectos filtrados por niche."""
    return _wrap(_list_projects, niche=niche, locale=locale)


def list_certificates(*, niche: str | None) -> list[dict[str, Any]]:
    """Devuelve los certificados filtrados por niche."""
    return _wrap(_list_certificates, niche=niche)


def list_awards(*, niche: str | None, locale: str) -> list[dict[str, Any]]:
    """Devuelve los premios filtrados por niche."""
    return _wrap(_list_awards, niche=niche, locale=locale)


def list_education(*, niche: str | None, locale: str) -> list[dict[str, Any]]:
    """Devuelve la educacion filtrada por niche."""
    return _wrap(_list_education, niche=niche, locale=locale)


def list_languages(*, niche: str | None, locale: str) -> list[dict[str, Any]]:
    """Devuelve los idiomas filtrados por niche."""
    return _wrap(_list_languages, niche=niche, locale=locale)


def list_references(*, niche: str | None, locale: str) -> list[dict[str, Any]]:
    """Devuelve las referencias filtradas por niche."""
    return _wrap(_list_references, niche=niche, locale=locale)


def list_skill_categories(
    *, niche: str | None, locale: str
) -> list[dict[str, Any]]:
    """Devuelve las categorias de skills filtradas por niche."""
    return _wrap(_list_skill_categories, niche=niche, locale=locale)
