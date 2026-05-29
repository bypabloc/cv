"""WebauthnRegisterVerifyIn exige `response` dict + challenge_id UUID.

Given un response que no es dict (string) o un challenge_id no-UUID,
When se valida con WebauthnRegisterVerifyIn,
Then pydantic ValidationError.
"""

import pytest
from pydantic import ValidationError

_CHALLENGE = '01900000-0000-7000-8000-000000000001'


def test_webauthn_register_verify_in_rejects_non_dict_response():
    from models.webauthn import WebauthnRegisterVerifyIn

    with pytest.raises(ValidationError) as exc:
        WebauthnRegisterVerifyIn(challenge_id=_CHALLENGE, response='not-a-dict')
    assert any(e['loc'] == ('response',) for e in exc.value.errors())


def test_webauthn_register_verify_in_rejects_bad_uuid():
    from models.webauthn import WebauthnRegisterVerifyIn

    with pytest.raises(ValidationError) as exc:
        WebauthnRegisterVerifyIn(challenge_id='not-a-uuid', response={})
    assert any(e['loc'] == ('challenge_id',) for e in exc.value.errors())


def test_webauthn_register_verify_in_accepts_valid():
    from models.webauthn import WebauthnRegisterVerifyIn

    model = WebauthnRegisterVerifyIn(
        challenge_id=_CHALLENGE,
        response={'id': 'x'},
        nickname='Mac',
    )
    assert model.response == {'id': 'x'}
    assert model.nickname == 'Mac'
