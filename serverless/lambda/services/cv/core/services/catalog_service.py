"""Catalog service del Lambda `cv` (operations admin) — catalogos para los selects.

`catalogs` lee los 3 vocabularios que la UI del admin necesita para
armar los selects de los forms: `tax_niches` (en orden de presentacion),
`cv_skills` y `tax_tech_tags`. Read-only: NO invalida cache.
"""

from __future__ import annotations

from typing import Any

from shared.db.models.cv.skill import Skill
from shared.db.models.taxonomy.catalog import Niche, TechTag
from shared.db.sa import select
from shared.db.session import db_session


def catalogs() -> dict[str, Any]:
    """Devuelve los catalogos (niches + skills + tech tags) para selects.

    Returns:
        `{'niches': [<slug>...], 'skills': [{'slug','name'}...],
        'techTags': [{'slug','name'}...]}` — niches en `display_order`,
        skills/techTags ordenados por slug.
    """
    with db_session() as session:
        niches = (
            session.execute(
                select(Niche.slug).order_by(Niche.display_order, Niche.slug)
            )
            .scalars()
            .all()
        )
        skills = session.execute(
            select(Skill.slug, Skill.name).order_by(Skill.slug)
        ).all()
        tech_tags = session.execute(
            select(TechTag.slug, TechTag.name).order_by(TechTag.slug)
        ).all()
    return {
        'niches': list(niches),
        'skills': [{'slug': slug, 'name': name} for slug, name in skills],
        'techTags': [
            {'slug': slug, 'name': name} for slug, name in tech_tags
        ],
    }
