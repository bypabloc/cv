"""RegisterStartIn rechaza cuando falta `email`.

Given un payload sin `email`,
When se valida con RegisterStartIn,
Then pydantic ValidationError.
"""

import pytest
from pydantic import ValidationError


def test_register_start_in_rejects_missing_email():
    from models.register import RegisterStartIn

    with pytest.raises(ValidationError) as exc:
        RegisterStartIn(cf_turnstile_response='token-xxx')

    errors = exc.value.errors()
    assert any(e['loc'] == ('email',) for e in errors)
