"""ReorderIn rechaza entity_type fuera del catalogo de 9 entidades.

Given entity_type 'profile' (no reordenable),
When se valida con ReorderIn,
Then ValidationError en entity_type."""

import pytest
from pydantic import ValidationError


def test_reorder_in_entity_type_enum():
    from models.content_simple import ReorderIn

    with pytest.raises(ValidationError) as exc:
        ReorderIn.model_validate({'entity_type': 'profile', 'niche': 'generic', 'ordered_slugs': ['a']})
    assert any(
        e['loc'][:1] == ('entity_type',) for e in exc.value.errors()
    ), f"esperaba error en entity_type pero fue: {exc.value.errors()}"
