"""Reorder service del Lambda `cv` (operations admin) — prioridades por niche.

`reorder` reescribe `tax_niche_priorities` del `(entity_type, niche)`
recibido: valida que `ordered_slugs` sea EXACTAMENTE el conjunto de slugs
asignados a ese niche (via la union `<entidad>_niches`) y delega la
reescritura ordenada a `shared.db.repositories.cv_write.
reorder_niche_priorities` (prioridad descendente con paso 10). Tras el
commit invalida el cache tag 'cv'.
"""

from __future__ import annotations

from typing import Any

from shared.db.models.cv.cv_entity import (
    Award,
    AwardNiche,
    Certificate,
    CertificateNiche,
    Endorsement,
    EndorsementNiche,
    Language,
    LanguageNiche,
    Publication,
    PublicationNiche,
)
from shared.db.models.cv.education import EducationEntry, EducationEntryNiche
from shared.db.models.cv.experience import Experience, ExperienceNiche
from shared.db.models.cv.project import Project, ProjectNiche
from shared.db.models.cv.skill import SkillCategory, SkillCategoryNiche
from shared.db.models.taxonomy.catalog import Niche
from shared.db.repositories.cv_write import reorder_niche_priorities
from shared.db.sa import select
from shared.db.session import db_session

from ._errors import ServiceError
from .content_service import invalidate_cv_cache

# entity_type -> (modelo, union <entidad>_niches, columna FK de la union).
# El entity_type string coincide con el usado por set_niche_priorities en
# cv_write_entities (asi el reorder toca las mismas filas que el upsert).
_REORDER_ENTITIES: dict[str, tuple[type, type, str]] = {
    'experience': (Experience, ExperienceNiche, 'experience_id'),
    'project': (Project, ProjectNiche, 'project_id'),
    'skill_category': (
        SkillCategory,
        SkillCategoryNiche,
        'skill_category_id',
    ),
    'certificate': (Certificate, CertificateNiche, 'certificate_id'),
    'award': (Award, AwardNiche, 'award_id'),
    'education': (EducationEntry, EducationEntryNiche, 'education_entry_id'),
    'language': (Language, LanguageNiche, 'language_id'),
    'endorsement': (Endorsement, EndorsementNiche, 'endorsement_id'),
    'publication': (Publication, PublicationNiche, 'publication_id'),
}


def reorder(
    *,
    entity_type: str,
    niche: str,
    ordered_slugs: list[str],
) -> dict[str, Any]:
    """Reescribe las prioridades del `(entity_type, niche)` segun el orden.

    Args:
        entity_type: clave de `_REORDER_ENTITIES`.
        niche: slug del niche cuyas prioridades se reescriben.
        ordered_slugs: TODOS los slugs de la entidad asignados a ese
            niche, en el orden de presentacion deseado (el primero queda
            con la prioridad mas alta).

    Returns:
        `{'entity_type', 'niche', 'reordered': <n>}`.

    Raises:
        ServiceError: 4404 NICHE_NOT_FOUND si el niche no existe; 1101
            REORDER_SLUGS_MISMATCH si `ordered_slugs` difiere del conjunto
            asignado (con faltantes/sobrantes en `detail`).
    """
    if entity_type not in _REORDER_ENTITIES:
        msg = f'entity_type desconocido: {entity_type!r}'
        raise ValueError(msg)
    model, union_model, entity_col = _REORDER_ENTITIES[entity_type]

    with db_session() as session:
        niche_id = session.execute(
            select(Niche.id).where(Niche.slug == niche)
        ).scalar_one_or_none()
        if niche_id is None:
            raise ServiceError(
                f'niche {niche!r} no existe',
                code=4404,
                error_code='NICHE_NOT_FOUND',
                detail={'niche': niche},
            )

        union_col = getattr(union_model, entity_col)
        rows = session.execute(
            select(model.slug, model.id)
            .join(union_model, union_col == model.id)
            .where(union_model.niche_id == niche_id)
        ).all()
        assigned: dict[str, str] = dict(rows)

        ordered_set = set(ordered_slugs)
        assigned_set = set(assigned)
        has_duplicates = len(ordered_slugs) != len(ordered_set)
        if ordered_set != assigned_set or has_duplicates:
            missing = sorted(assigned_set - ordered_set)
            extra = sorted(ordered_set - assigned_set)
            raise ServiceError(
                'ordered_slugs no coincide con las entidades del niche: '
                f'faltantes={missing} sobrantes={extra}',
                code=1101,
                error_code='REORDER_SLUGS_MISMATCH',
                detail={'missing': missing, 'extra': extra},
            )

        ordered_ids = [assigned[slug] for slug in ordered_slugs]
        reorder_niche_priorities(session, entity_type, niche_id, ordered_ids)

    invalidate_cv_cache()
    return {
        'entity_type': entity_type,
        'niche': niche,
        'reordered': len(ordered_ids),
    }
