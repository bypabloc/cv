"""ProfileDeleteAccountIn.confirm exige el sentinel exacto.

Given un confirm distinto del sentinel ('WRONG'),
When se valida con ProfileDeleteAccountIn,
Then pydantic ValidationError; y 'DELETE-MY-ACCOUNT' queda en .confirm.
"""

import pytest
from pydantic import ValidationError


def test_profile_delete_account_in_sentinel_exact():
    from models.profile import ProfileDeleteAccountIn

    with pytest.raises(ValidationError) as exc:
        ProfileDeleteAccountIn.model_validate({'confirm': 'WRONG'})
    assert any(
        e['loc'] == ('confirm',) for e in exc.value.errors()
    ), 'confirm WRONG should fail but did not'

    parsed = ProfileDeleteAccountIn.model_validate(
        {'confirm': 'DELETE-MY-ACCOUNT'}
    )
    assert parsed.confirm == 'DELETE-MY-ACCOUNT'
