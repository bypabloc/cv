"""ExperienceIn rechaza seniority fuera del enum.

Given seniority 'principal' (no existe en el enum),
When se valida con ExperienceIn,
Then ValidationError en seniority."""

import pytest
from pydantic import ValidationError


def test_experience_in_seniority_enum():
    from models.content import ExperienceIn

    with pytest.raises(ValidationError) as exc:
        ExperienceIn.model_validate({'slug': 'ok-slug', 'role': {'es': 'x'}, 'company': 'C', 'country': 'CL', 'start': '2024', 'seniority': 'principal'})
    assert any(
        e['loc'][:1] == ('seniority',) for e in exc.value.errors()
    ), f"esperaba error en seniority pero fue: {exc.value.errors()}"
