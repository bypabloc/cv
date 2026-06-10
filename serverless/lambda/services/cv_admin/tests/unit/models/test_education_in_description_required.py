"""EducationIn exige description bilingue.

Given una educacion sin description,
When se valida con EducationIn,
Then ValidationError en description."""

import pytest
from pydantic import ValidationError


def test_education_in_description_required():
    from models.content_simple import EducationIn

    with pytest.raises(ValidationError) as exc:
        EducationIn.model_validate({'slug': 'udemy', 'institution': 'Udemy', 'start': '2017'})
    assert any(
        e['loc'][:1] == ('description',) for e in exc.value.errors()
    ), f"esperaba error en description pero fue: {exc.value.errors()}"
