"""Content service del Lambda `cv` (operations admin) — upserts y deletes del CV.

Abre LA transaccion (`db_session()`), valida que los niches referenciados
existan en el catalogo (UNKNOWN_NICHE antes de escribir), delega la
escritura compuesta a `shared.db.repositories.cv_write_entities` (la
MISMA capa que usa el seed de la Lambda `db`) y, tras el commit, invalida
el cache DynamoDB por tag `'cv'` (las lecturas del Lambda `cv` usan
`@cached(tags=['cv'])`).

Los upserts/deletes se resuelven POR NOMBRE contra `cv_write_entities`
(`getattr` en cada llamada) para que los tests intercepten con
`monkeypatch` la funcion real.
"""

from __future__ import annotations

from typing import Any

import shared.db.repositories.cv_write_entities as cv_write_entities
from shared.cache.client import DynamoDBCache
from shared.db.repositories.cv_write import resolve_niches
from shared.db.session import db_session

from ._errors import ServiceError

# Tag que agrupa TODAS las keys cacheadas del Lambda cv (ver
# services/cv/core/services/cv_service.py `_CV_TAGS`).
_CV_CACHE_TAG = 'cv'

# Entidades con upsert compuesto propio en cv_write_entities.
_UPSERT_ENTITIES = frozenset({
    'profile',
    'experience',
    'project',
    'skill_category',
    'certificate',
    'award',
    'education',
    'endorsement',
    'language',
    'publication',
})

# Entidades con delete dedicado (las demas van por delete_simple).
_DEDICATED_DELETES = frozenset({'experience', 'project', 'skill_category'})


def invalidate_cv_cache() -> int:
    """Invalida (soft-delete TTL=0) todos los items del cache con tag 'cv'.

    Se llama DESPUES del commit: una invalidacion sin commit dejaria al
    Lambda `cv` recacheando el estado viejo.
    """
    return DynamoDBCache().invalidate(tag=_CV_CACHE_TAG)


def _ensure_known_niches(
    data: dict[str, Any],
    niche_ids: dict[str, str],
) -> None:
    """Valida que `niches` y las keys de `priority` existan en el catalogo.

    Un slug desconocido NO se ignora silenciosamente en la API (el seed si
    lo tolera): se rechaza ANTES de escribir.

    Raises:
        ServiceError: 1100 UNKNOWN_NICHE con los slugs desconocidos.
    """
    referenced = {*(data.get('niches') or []), *(data.get('priority') or {})}
    unknown = sorted(referenced - set(niche_ids))
    if unknown:
        raise ServiceError(
            f'niches desconocidos: {unknown}',
            code=1100,
            error_code='UNKNOWN_NICHE',
            detail={'unknown_niches': unknown},
        )


def upsert_entity(*, entity: str, data: dict[str, Any]) -> dict[str, Any]:
    """Upsert completo de una entidad del CV en UNA transaccion.

    Args:
        entity: clave de `_UPSERT_ENTITIES` (ej. 'experience').
        data: payload validado por el modelo Pydantic, en el shape YAML
            del seed (camelCase, bloques bilingues).

    Returns:
        `{'entity': <slug|handle>, 'id': <uuid>}`.

    Raises:
        ServiceError: 1100 UNKNOWN_NICHE si un niche referenciado no
            existe en el catalogo (rollback, nada se escribe); 1102
            INVALID_FIELD_VALUE si un valor pasa el shape del modelo
            pero no es coercible (ej. fecha 'YYYY-13' que revienta
            `coerce_date`) — 400 de contrato, nunca un 500 unhandled.
    """
    if entity not in _UPSERT_ENTITIES:
        msg = f'entidad desconocida: {entity!r}'
        raise ValueError(msg)
    upsert_fn = getattr(cv_write_entities, f'upsert_{entity}')
    with db_session() as session:
        niche_ids = resolve_niches(session)
        _ensure_known_niches(data, niche_ids)
        try:
            entity_id = upsert_fn(session, data, niche_ids)
        except ValueError as exc:
            raise ServiceError(
                f'valor invalido en {entity}: {exc}',
                code=1102,
                error_code='INVALID_FIELD_VALUE',
            ) from exc
    invalidate_cv_cache()
    natural_key = data['handle'] if entity == 'profile' else data['slug']
    return {'entity': natural_key, 'id': str(entity_id)}


def delete_entity(*, entity: str, slug: str) -> dict[str, Any]:
    """Delete completo de una entidad del CV (hijos + uniones + i18n +
    priorities) en UNA transaccion.

    Args:
        entity: tipo de entidad ('experience', 'project', 'skill_category'
            o una clave de `cv_write_entities.SIMPLE_ENTITIES`).
        slug: clave natural de la fila a borrar.

    Returns:
        `{'entity': <slug>, 'deleted': True}`.

    Raises:
        ServiceError: 4404 SLUG_NOT_FOUND si el slug no existe.
    """
    with db_session() as session:
        if entity in _DEDICATED_DELETES:
            delete_fn = getattr(cv_write_entities, f'delete_{entity}')
            deleted = delete_fn(session, slug)
        else:
            deleted = cv_write_entities.delete_simple(session, entity, slug)
        if not deleted:
            raise ServiceError(
                f'{entity} con slug {slug!r} no existe',
                code=4404,
                error_code='SLUG_NOT_FOUND',
                detail={'entity': entity, 'slug': slug},
            )
    invalidate_cv_cache()
    return {'entity': slug, 'deleted': True}
