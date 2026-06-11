"""ExperienceIn rechaza fechas fuera de YYYY[-MM[-DD]].

Given start '01-2024' (orden invertido),
When se valida con ExperienceIn,
Then ValidationError en start."""

import pytest
from pydantic import ValidationError


def test_experience_in_bad_date():
    from models.content import ExperienceIn

    with pytest.raises(ValidationError) as exc:
        ExperienceIn.model_validate({'slug': 'ok-slug', 'role': {'es': 'x'}, 'company': 'C', 'country': 'CL', 'start': '01-2024', 'seniority': 'senior'})
    assert any(
        e['loc'][:1] == ('start',) for e in exc.value.errors()
    ), f"esperaba error en start pero fue: {exc.value.errors()}"
