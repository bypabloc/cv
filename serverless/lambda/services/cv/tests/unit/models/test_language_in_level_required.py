"""LanguageIn exige level bilingue.

Given un idioma sin level,
When se valida con LanguageIn,
Then ValidationError en level."""

import pytest
from pydantic import ValidationError


def test_language_in_level_required():
    from models.content_simple import LanguageIn

    with pytest.raises(ValidationError) as exc:
        LanguageIn.model_validate({'slug': 'english', 'name': {'es': 'Ingles'}})
    assert any(
        e['loc'][:1] == ('level',) for e in exc.value.errors()
    ), f"esperaba error en level pero fue: {exc.value.errors()}"
