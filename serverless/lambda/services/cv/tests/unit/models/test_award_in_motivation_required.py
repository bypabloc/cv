"""AwardIn exige motivation bilingue.

Given un premio sin motivation,
When se valida con AwardIn,
Then ValidationError en motivation."""

import pytest
from pydantic import ValidationError


def test_award_in_motivation_required():
    from models.content_simple import AwardIn

    with pytest.raises(ValidationError) as exc:
        AwardIn.model_validate({'slug': 'a', 'title': {'es': 't'}, 'issuer': 'I', 'date': '2024-01'})
    assert any(
        e['loc'][:1] == ('motivation',) for e in exc.value.errors()
    ), f"esperaba error en motivation pero fue: {exc.value.errors()}"
