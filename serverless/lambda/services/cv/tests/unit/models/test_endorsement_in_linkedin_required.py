"""EndorsementIn exige linkedin.

Given una recomendacion sin linkedin,
When se valida con EndorsementIn,
Then ValidationError en linkedin."""

import pytest
from pydantic import ValidationError


def test_endorsement_in_linkedin_required():
    from models.content_simple import EndorsementIn

    with pytest.raises(ValidationError) as exc:
        EndorsementIn.model_validate({'slug': 'e', 'name': 'N', 'role': 'R', 'relation': {'es': 'r'}})
    assert any(
        e['loc'][:1] == ('linkedin',) for e in exc.value.errors()
    ), f"esperaba error en linkedin pero fue: {exc.value.errors()}"
