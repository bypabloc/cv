"""
Given un user existente y campos parciales whitelisted,
When se llama update_profile con display_name y locale,
Then setea solo esos atributos, hace flush y retorna el user.
"""

from unittest.mock import MagicMock

import pytest
from shared.db.repositories.auth_users import update_profile

pytestmark = pytest.mark.unit


def test_update_profile_sets_only_whitelisted_fields():
    # Arrange
    session = MagicMock()
    user = MagicMock()
    session.get.return_value = user

    # Act
    result = update_profile(
        session, user_id='u1', display_name='X', locale='es',
    )

    # Assert
    assert result is user
    assert user.display_name == 'X'
    assert user.locale == 'es'
    session.flush.assert_called_once()
