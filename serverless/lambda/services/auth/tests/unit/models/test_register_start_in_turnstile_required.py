"""RegisterStartIn rechaza cuando falta `cf_turnstile_response`.

Given un payload sin cf_turnstile_response,
When se valida con RegisterStartIn,
Then pydantic ValidationError.
"""

import pytest
from pydantic import ValidationError


def test_register_start_in_rejects_missing_turnstile():
    from models.register import RegisterStartIn

    with pytest.raises(ValidationError) as exc:
        RegisterStartIn(email='valid@example.com')

    errors = exc.value.errors()
    assert any(e['loc'] == ('cf_turnstile_response',) for e in errors)
