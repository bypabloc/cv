"""SkillCategoryIn rechaza kind fuera de technical|soft.

Given kind 'hybrid',
When se valida con SkillCategoryIn,
Then ValidationError en kind."""

import pytest
from pydantic import ValidationError


def test_skill_category_in_kind_enum():
    from models.content import SkillCategoryIn

    with pytest.raises(ValidationError) as exc:
        SkillCategoryIn.model_validate({'slug': 's', 'name': {'es': 'n'}, 'kind': 'hybrid', 'skills': []})
    assert any(
        e['loc'][:1] == ('kind',) for e in exc.value.errors()
    ), f"esperaba error en kind pero fue: {exc.value.errors()}"
