"""SessionRefreshIn rechaza refresh_token con menos de 20 chars.

Given un refresh_token de 19 chars,
When se valida con SessionRefreshIn,
Then pydantic ValidationError.
"""

import pytest
from pydantic import ValidationError


def test_session_refresh_in_rejects_short_token():
    from models.session import SessionRefreshIn

    with pytest.raises(ValidationError) as exc:
        SessionRefreshIn(refresh_token='a' * 19)

    errors = exc.value.errors()
    assert any(e['loc'] == ('refresh_token',) for e in errors)
