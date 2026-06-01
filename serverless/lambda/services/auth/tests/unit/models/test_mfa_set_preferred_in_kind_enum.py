"""MfaSetPreferredIn solo acepta kind in {'totp', 'email_code'}.

Given un kind fuera del Literal,
When se valida con MfaSetPreferredIn,
Then pydantic ValidationError.
"""

import pytest
from pydantic import ValidationError


def test_mfa_set_preferred_in_rejects_unknown_kind():
    from models.mfa import MfaSetPreferredIn

    for kind in ['webauthn', 'sms', '', 'TOTP']:
        with pytest.raises(ValidationError) as exc:
            MfaSetPreferredIn(kind=kind)
        assert any(e['loc'] == ('kind',) for e in exc.value.errors()), (
            f'kind {kind!r} should fail but did not'
        )


def test_mfa_set_preferred_in_accepts_valid_kinds():
    from models.mfa import MfaSetPreferredIn

    assert MfaSetPreferredIn(kind='totp').kind == 'totp'
    assert MfaSetPreferredIn(kind='email_code').kind == 'email_code'
