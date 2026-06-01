"""WebauthnDeleteCredentialIn exige credential_id UUID.

Given un credential_id que no es UUID,
When se valida con WebauthnDeleteCredentialIn,
Then pydantic ValidationError.
"""

import pytest
from pydantic import ValidationError


def test_webauthn_delete_credential_in_rejects_non_uuid():
    from models.webauthn import WebauthnDeleteCredentialIn

    with pytest.raises(ValidationError) as exc:
        WebauthnDeleteCredentialIn(credential_id='not-a-uuid')
    assert any(e['loc'] == ('credential_id',) for e in exc.value.errors())


def test_webauthn_delete_credential_in_accepts_uuid():
    from uuid import UUID

    from models.webauthn import WebauthnDeleteCredentialIn

    cid = '01900000-0000-7000-8000-000000000002'
    model = WebauthnDeleteCredentialIn(credential_id=cid)
    assert model.credential_id == UUID(cid)
