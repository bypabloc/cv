"""reorder rechaza un entity_type fuera del registro (guard interno).

Given entity_type='profile' (no reordenable),
When se invoca reorder,
Then ValueError (el modelo Pydantic ya lo previene; guard de defensa).
"""

import pytest


def test_reorder_unknown_entity_type_raises():
    from services import reorder_service

    with pytest.raises(ValueError, match='entity_type desconocido'):
        reorder_service.reorder(
            entity_type='profile', niche='generic', ordered_slugs=['a'],
        )
