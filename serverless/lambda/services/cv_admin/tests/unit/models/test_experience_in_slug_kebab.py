"""ExperienceIn rechaza slug no-kebab-case.

Given slug con mayusculas/underscore,
When se valida con ExperienceIn,
Then ValidationError en slug."""

import pytest
from pydantic import ValidationError


def test_experience_in_slug_kebab():
    from models.content import ExperienceIn

    with pytest.raises(ValidationError) as exc:
        ExperienceIn.model_validate({'slug': 'Bad_Slug', 'role': {'es': 'x'}, 'company': 'C', 'country': 'CL', 'start': '2024-01', 'seniority': 'senior'})
    assert any(
        e['loc'][:1] == ('slug',) for e in exc.value.errors()
    ), f"esperaba error en slug pero fue: {exc.value.errors()}"
