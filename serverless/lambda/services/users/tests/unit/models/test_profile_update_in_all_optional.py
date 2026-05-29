"""ProfileUpdateIn admite un payload vacio (todos los campos opcionales).

Given un payload vacio {},
When se valida con ProfileUpdateIn,
Then la instancia es valida y todos los campos editables quedan en None.
"""


def test_profile_update_in_all_optional():
    from models.profile import ProfileUpdateIn

    parsed = ProfileUpdateIn.model_validate({})

    assert parsed.display_name is None
    assert parsed.locale is None
    assert parsed.timezone is None
    assert parsed.marketing_consent is None
    assert parsed.privacy_policy_version is None
