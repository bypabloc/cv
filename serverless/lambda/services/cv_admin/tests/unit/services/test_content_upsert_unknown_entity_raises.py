"""upsert_entity rechaza una entidad fuera del registro (guard interno).

Given entity='visitas' (no existe en _UPSERT_ENTITIES),
When se invoca content_service.upsert_entity,
Then ValueError (error de programacion, no de negocio).
"""

import pytest


def test_content_upsert_unknown_entity_raises():
    from services import content_service

    with pytest.raises(ValueError, match='entidad desconocida'):
        content_service.upsert_entity(entity='visitas', data={'slug': 'x'})
