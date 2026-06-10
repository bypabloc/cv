"""ReorderIn exige ordered_slugs no vacia.

Given ordered_slugs [],
When se valida con ReorderIn,
Then ValidationError en ordered_slugs."""

import pytest
from pydantic import ValidationError


def test_reorder_in_empty_slugs():
    from models.content_simple import ReorderIn

    with pytest.raises(ValidationError) as exc:
        ReorderIn.model_validate({'entity_type': 'experience', 'niche': 'generic', 'ordered_slugs': []})
    assert any(
        e['loc'][:1] == ('ordered_slugs',) for e in exc.value.errors()
    ), f"esperaba error en ordered_slugs pero fue: {exc.value.errors()}"
