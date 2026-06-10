"""BiLang exige al menos un locale (es o en).

Given un bloque bilingue vacio {},
When se valida con BiLang,
Then ValidationError (el model_validator exige es o en).
"""

import pytest
from pydantic import ValidationError


def test_bilang_at_least_one_locale():
    from models._common import BiLang

    with pytest.raises(ValidationError) as exc:
        BiLang.model_validate({})
    assert 'al menos un locale' in str(exc.value)
