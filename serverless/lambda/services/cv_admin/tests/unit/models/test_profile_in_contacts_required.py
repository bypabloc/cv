"""ProfileIn exige el bloque contacts.

Given un profile sin contacts,
When se valida con ProfileIn,
Then ValidationError en contacts."""

import pytest
from pydantic import ValidationError


def test_profile_in_contacts_required():
    from models.content import ProfileIn

    with pytest.raises(ValidationError) as exc:
        ProfileIn.model_validate({'name': 'P', 'handle': 'bypabloc', 'headline': {'es': 'h'}, 'summary': {'es': 's'}, 'location': 'Lima', 'avatarUrl': 'https://x/a.avif'})
    assert any(
        e['loc'][:1] == ('contacts',) for e in exc.value.errors()
    ), f"esperaba error en contacts pero fue: {exc.value.errors()}"
