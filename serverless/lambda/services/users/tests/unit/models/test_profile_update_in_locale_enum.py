"""ProfileUpdateIn.locale solo acepta el Literal {'es', 'en'}.

Given un locale fuera del Literal ('fr'),
When se valida con ProfileUpdateIn,
Then pydantic ValidationError; y un locale valido ('es') queda en .locale.
"""

import pytest
from pydantic import ValidationError


def test_profile_update_in_locale_enum():
    from models.profile import ProfileUpdateIn

    with pytest.raises(ValidationError) as exc:
        ProfileUpdateIn.model_validate({'locale': 'fr'})
    assert any(
        e['loc'] == ('locale',) for e in exc.value.errors()
    ), 'locale fr should fail but did not'

    parsed = ProfileUpdateIn.model_validate({'locale': 'es'})
    assert parsed.locale == 'es'
